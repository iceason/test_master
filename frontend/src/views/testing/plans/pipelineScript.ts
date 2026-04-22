export interface StepData {
  name: string
  script: string
  timeout: number
  on_failure: string
}

export interface PipelineConfig {
  agentLabel?: string
  gitRepoUrl?: string
  gitBranch?: string
  gitCredentialId?: string
  workspaceCleanup?: boolean
  reportEnabled?: boolean
  reportCommand?: string
  environmentVariables?: { key: string; value: string }[]
}

const AUTO_MARKER = '// [auto-generated]'

function escapeGroovy(text: string): string {
  return text.replace(/\\/g, '\\\\').replace(/'/g, "\\'")
}

function escapeGroovyTriple(text: string): string {
  const result: string[] = []
  let consecutiveQuotes = 0
  for (const ch of text) {
    if (ch === '\\') {
      result.push('\\\\')
      consecutiveQuotes = 0
    } else if (ch === "'") {
      consecutiveQuotes++
      if (consecutiveQuotes === 3) {
        result.push("\\'")
        consecutiveQuotes = 0
      } else {
        result.push("'")
      }
    } else {
      consecutiveQuotes = 0
      result.push(ch)
    }
  }
  if (consecutiveQuotes > 0) {
    for (let i = result.length - 1; i >= 0; i--) {
      if (result[i] === "'") {
        result[i] = "\\'"
        break
      }
    }
  }
  return result.join('')
}

function indent(text: string, n: number): string {
  const prefix = ' '.repeat(n)
  return text
    .split('\n')
    .map((line) => (line.trim() ? prefix + line : line))
    .join('\n')
}

function formatSh(script: string): string {
  const lines = script.split('\n')
  if (lines.length === 1 && !script.includes("'")) {
    return `sh '${escapeGroovy(script)}'`
  }
  const escaped = escapeGroovyTriple(script)
  if (!escaped.includes('\n')) {
    return `sh '''${escaped}'''`
  }
  return `sh '''\n${indent(escaped, 4)}\n'''`
}

export function generateJenkinsfile(steps: StepData[], config: PipelineConfig = {}): string {
  const lines: string[] = []
  lines.push('pipeline {')

  if (config.agentLabel) {
    lines.push(`    agent { label '${escapeGroovy(config.agentLabel)}' }`)
  } else {
    lines.push('    agent any')
  }

  const envVars = (config.environmentVariables || []).filter((e) => e.key?.trim())
  if (envVars.length) {
    lines.push('')
    lines.push('    environment {')
    for (const ev of envVars) {
      const safeKey = ev.key.trim().replace(/[^A-Za-z0-9_]/g, '_')
      lines.push(`        ${safeKey} = '${escapeGroovy(ev.value || '')}'`)
    }
    lines.push('    }')
  }

  lines.push('')
  lines.push('    stages {')

  if (config.gitRepoUrl) {
    lines.push(`        ${AUTO_MARKER}`)
    lines.push("        stage('Git Checkout') {")
    lines.push('            steps {')
    if (config.workspaceCleanup !== false) {
      lines.push('                cleanWs()')
    }
    const gitArgs: string[] = [
      `url: '${escapeGroovy(config.gitRepoUrl)}'`,
      `branch: '${escapeGroovy(config.gitBranch || 'main')}'`,
    ]
    if (config.gitCredentialId) {
      gitArgs.push(`credentialsId: '${escapeGroovy(config.gitCredentialId)}'`)
    }
    lines.push('                git(')
    for (let i = 0; i < gitArgs.length; i++) {
      const comma = i < gitArgs.length - 1 ? ',' : ''
      lines.push(`                    ${gitArgs[i]}${comma}`)
    }
    lines.push('                )')
    lines.push('            }')
    lines.push('        }')
    lines.push('')
  }

  if (!steps.length) {
    lines.push(`        ${AUTO_MARKER}`)
    lines.push("        stage('Default') {")
    lines.push('            steps {')
    lines.push("                sh 'echo \"No build steps configured.\"'")
    lines.push('            }')
    lines.push('        }')
  } else {
    for (let idx = 0; idx < steps.length; idx++) {
      const step = steps[idx]!
      const name = step.name || 'Unnamed'
      const timeout = step.timeout || 120
      const script = step.script || 'echo "no script"'

      lines.push(`        stage('${escapeGroovy(name)}') {`)
      lines.push('            steps {')

      let body = formatSh(script)
      body = `timeout(time: ${timeout}, unit: 'SECONDS') {\n${indent(body, 4)}\n}`

      if (step.on_failure === 'retry') {
        body = `retry(2) {\n${indent(body, 4)}\n}`
      } else if (step.on_failure === 'continue') {
        body = `catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {\n${indent(body, 4)}\n}`
      }

      lines.push(indent(body, 16))
      lines.push('            }')
      lines.push('        }')
      if (idx < steps.length - 1) lines.push('')
    }
  }

  lines.push('    }')

  if (config.reportEnabled && config.reportCommand) {
    const reportSh = formatSh(config.reportCommand)
    lines.push('')
    lines.push('    post {')
    lines.push('        always {')
    lines.push(indent(reportSh, 12))
    lines.push('        }')
    lines.push('    }')
  }

  lines.push('}')
  lines.push('')
  return lines.join('\n')
}

export function parseJenkinsfile(script: string): { steps: StepData[]; warnings: string[] } {
  const steps: StepData[] = []
  const warnings: string[] = []

  const stageRegex = /stage\s*\(\s*(['"])([^]*?)\1\s*\)\s*\{/g
  const stagePositions: { name: string; bodyStart: number; isAuto: boolean }[] = []
  let match: RegExpExecArray | null

  while ((match = stageRegex.exec(script)) !== null) {
    const precedingText = script.slice(Math.max(0, match.index - 80), match.index)
    const isAuto = precedingText.includes('[auto-generated]')
    const openBrace = match.index + match[0].length - 1
    stagePositions.push({ name: match[2] ?? '', bodyStart: openBrace, isAuto })
  }

  if (!stagePositions.length) {
    warnings.push('No stages found in Jenkinsfile')
    return { steps, warnings }
  }

  for (const stage of stagePositions) {
    if (stage.isAuto) continue
    const stageBody = extractBlock(script, stage.bodyStart)
    if (!stageBody) {
      warnings.push(`Could not parse stage '${stage.name}'`)
      continue
    }

    let timeout = 120
    const timeoutMatch = stageBody.match(/timeout\s*\(\s*time\s*:\s*(\d+)/)
    if (timeoutMatch?.[1]) timeout = parseInt(timeoutMatch[1], 10)

    let onFailure = 'stop'
    if (stageBody.includes('retry(')) onFailure = 'retry'
    else if (stageBody.includes('catchError(')) onFailure = 'continue'

    let scriptContent = extractShScript(stageBody)
    if (!scriptContent) scriptContent = extractStepsBlockContent(stageBody)

    const name = unescapeGroovy(stage.name)
    steps.push({ name, script: (scriptContent || '').trim(), timeout, on_failure: onFailure })
  }

  return { steps, warnings }
}

function extractStepsBlockContent(stageBody: string): string {
  const stepsIdx = stageBody.search(/\bsteps\s*\{/)
  if (stepsIdx === -1) return ''
  const braceIdx = stageBody.indexOf('{', stepsIdx)
  const content = extractBlock(stageBody, braceIdx)
  if (!content) return ''
  const lines = content.split('\n').filter(l => l.trim().length > 0)
  if (!lines.length) return ''
  const minIndent = Math.min(...lines.map(l => l.match(/^(\s*)/)![0].length))
  return lines.map(l => l.slice(minIndent)).join('\n')
}

function extractShScript(body: string): string {
  const tripleStart = body.search(/\bsh\s+'''/)
  if (tripleStart !== -1) {
    const quoteStart = body.indexOf("'''", tripleStart)
    const content = extractTripleQuoted(body, quoteStart)
    if (content !== null) return unescapeGroovy(content)
  }
  const singleMatch = body.match(/\bsh\s+'([^']*)'/)
  if (singleMatch?.[1]) return unescapeGroovy(singleMatch[1])

  const batTripleStart = body.search(/\bbat\s+'''/)
  if (batTripleStart !== -1) {
    const quoteStart = body.indexOf("'''", batTripleStart)
    const content = extractTripleQuoted(body, quoteStart)
    if (content !== null) return unescapeGroovy(content)
  }
  const batSingle = body.match(/\bbat\s+'([^']*)'/)
  if (batSingle?.[1]) return unescapeGroovy(batSingle[1])
  return ''
}

function extractTripleQuoted(text: string, pos: number): string | null {
  if (text.slice(pos, pos + 3) !== "'''") return null
  let i = pos + 3
  while (i < text.length) {
    if (text[i] === '\\' && i + 1 < text.length) { i += 2; continue }
    if (text[i] === "'" && text[i + 1] === "'" && text[i + 2] === "'") {
      return text.slice(pos + 3, i)
    }
    i++
  }
  return null
}

function unescapeGroovy(text: string): string {
  return text.replace(/\\'/g, "'").replace(/\\\\/g, '\\')
}

function extractBlock(text: string, openBracePos: number): string | null {
  if (text[openBracePos] !== '{') return null
  let depth = 0
  let i = openBracePos
  while (i < text.length) {
    const ch = text[i]
    if (ch === '\\') { i += 2; continue }
    if (ch === "'" && text[i + 1] === "'" && text[i + 2] === "'") {
      i += 3
      while (i < text.length) {
        if (text[i] === '\\') { i += 2; continue }
        if (text[i] === "'" && text[i + 1] === "'" && text[i + 2] === "'") { i += 3; break }
        i++
      }
      continue
    }
    if (ch === "'") {
      i++
      while (i < text.length && text[i] !== "'") {
        if (text[i] === '\\') i++
        i++
      }
      i++
      continue
    }
    if (ch === '{') depth++
    else if (ch === '}') {
      depth--
      if (depth === 0) return text.slice(openBracePos + 1, i)
    }
    i++
  }
  return null
}
