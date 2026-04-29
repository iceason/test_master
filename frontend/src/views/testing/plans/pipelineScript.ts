export interface StepData {
  name: string
  script: string
  timeout: number
  on_failure: string
}

export interface PipelineConfig {
  osType?: string
  agentLabel?: string
  gitRepoUrl?: string
  gitBranch?: string
  gitCredentialId?: string
  workspaceCleanup?: boolean
  reportEnabled?: boolean
  reportResultsDir?: string
  reportCommand?: string
  environmentVariables?: { key: string; value: string }[]
  backendBaseUrl?: string
  buildPlanId?: number | null
  existingJenkinsfileText?: string
}

const AUTO_MARKER = '// [auto-generated]'
export const REPORT_UPLOAD_MARK_START = '// [testmaster:auto-report-upload:start]'
export const REPORT_UPLOAD_MARK_END = '// [testmaster:auto-report-upload:end]'

export function buildDefaultReportCommand(
  osType: string,
  reportResultsDir = 'allure-results'
): string {
  const os = (osType || 'linux').toLowerCase()
  const dir = (reportResultsDir || 'allure-results').trim() || 'allure-results'
  if (os === 'windows') {
    return (
      '@echo off\n' +
      `set "REPORT_DIR=${dir}"\n` +
      'if exist "%REPORT_DIR%" (\n' +
      '  if exist report.zip del /f /q report.zip\n' +
      "  powershell -NoProfile -Command \"Compress-Archive -Path '%REPORT_DIR%\\*' -DestinationPath 'report.zip' -Force\"\n" +
      '  curl.exe -f -X POST -F "report=@report.zip" "%BACKEND_BASE_URL%/api/upload-report/%EXECUTION_ID%/"\n' +
      ') else (\n' +
      '  echo [TestMaster] Allure results dir not found, skip report upload.\n' +
      ')'
    )
  }
  return (
    `REPORT_DIR="${dir}"\n` +
    'if [ -d "$REPORT_DIR" ]; then\n' +
    '  rm -f report.zip\n' +
    '  zip -r report.zip "$REPORT_DIR"\n' +
    '  curl -f -X POST -F "report=@report.zip" "$BACKEND_BASE_URL/api/upload-report/$EXECUTION_ID/"\n' +
    'else\n' +
    '  echo "[TestMaster] Allure results dir not found, skip report upload."\n' +
    'fi'
  )
}

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

function formatShellCommand(script: string, osType?: string): string {
  const cmd = (osType || '').toLowerCase() === 'windows' ? 'bat' : 'sh'
  const lines = script.split('\n')
  if (lines.length === 1 && !script.includes("'")) {
    return `${cmd} '${escapeGroovy(script)}'`
  }
  const escaped = escapeGroovyTriple(script)
  if (!escaped.includes('\n')) {
    return `${cmd} '''${escaped}'''`
  }
  return `${cmd} '''\n${indent(escaped, 4)}\n'''`
}

function parseEnvironmentAssignments(script: string): Map<string, string> {
  const envMap = new Map<string, string>()
  if (!script) return envMap
  const envStart = script.search(/\benvironment\s*\{/)
  if (envStart === -1) return envMap
  const braceStart = script.indexOf('{', envStart)
  if (braceStart === -1) return envMap
  const envBody = extractBlock(script, braceStart)
  if (!envBody) return envMap

  const lineRegex = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$/gm
  let m: RegExpExecArray | null
  while ((m = lineRegex.exec(envBody)) !== null) {
    const key = m[1]?.trim()
    let raw = (m[2] || '').trim()
    if (!key) continue
    if ((raw.startsWith("'") && raw.endsWith("'")) || (raw.startsWith('"') && raw.endsWith('"'))) {
      raw = raw.slice(1, -1)
    }
    envMap.set(key, unescapeGroovy(raw))
  }
  return envMap
}

function buildMergedEnvironmentMap(
  config: PipelineConfig,
  baseScript: string
): Map<string, string> {
  const backendUrl = (config.backendBaseUrl || 'http://127.0.0.1:8000').replace(/\/+$/, '')
  const envVars = (config.environmentVariables || []).filter((e) => e.key?.trim())
  const envMap = parseEnvironmentAssignments(baseScript || '')
  const setIfMissing = (k: string, v: string) => {
    if (!envMap.has(k)) envMap.set(k, v)
  }
  setIfMissing('BACKEND_BASE_URL', backendUrl)
  if (config.buildPlanId != null && config.buildPlanId !== undefined) {
    setIfMissing('BUILD_PLAN_ID', String(config.buildPlanId))
  }
  // EXECUTION_ID is required by report upload callback flow.
  setIfMissing('EXECUTION_ID', '${params.EXECUTION_ID}')
  for (const ev of envVars) {
    const safeKey = ev.key.trim().replace(/[^A-Za-z0-9_]/g, '_')
    if (!safeKey) continue
    envMap.set(safeKey, ev.value || '')
  }
  return envMap
}

function renderEnvironmentBlock(envMap: Map<string, string>): string {
  const lines: string[] = []
  lines.push('    environment {')
  for (const [k, v] of envMap.entries()) {
    if (
      k === 'EXECUTION_ID' &&
      (v.includes('${params.EXECUTION_ID}') || v.includes('params.EXECUTION_ID'))
    ) {
      lines.push('        EXECUTION_ID = "${params.EXECUTION_ID}"')
      continue
    }
    lines.push(`        ${k} = '${escapeGroovy(v)}'`)
  }
  lines.push('    }')
  return lines.join('\n')
}

export function upsertJenkinsfileEnvironment(script: string, config: PipelineConfig = {}): string {
  if (!script || !script.trim()) return script
  const envMap = buildMergedEnvironmentMap(config, script)
  const envBlock = renderEnvironmentBlock(envMap)

  const envStart = script.search(/\benvironment\s*\{/)
  if (envStart !== -1) {
    const braceStart = script.indexOf('{', envStart)
    if (braceStart !== -1) {
      const body = extractBlock(script, braceStart)
      if (body !== null) {
        const envEnd = braceStart + body.length + 1
        return `${script.slice(0, envStart)}${envBlock}${script.slice(envEnd + 1)}`
      }
    }
  }

  const paramsStart = script.search(/\bparameters\s*\{/)
  if (paramsStart !== -1) {
    const braceStart = script.indexOf('{', paramsStart)
    if (braceStart !== -1) {
      const body = extractBlock(script, braceStart)
      if (body !== null) {
        const paramsEnd = braceStart + body.length + 1
        const insertPos = paramsEnd + 1
        return `${script.slice(0, insertPos)}\n\n${envBlock}${script.slice(insertPos)}`
      }
    }
  }

  const agentMatch = script.match(/^\s*agent[^\n]*$/m)
  if (agentMatch && agentMatch.index != null) {
    const insertPos = (agentMatch.index || 0) + agentMatch[0].length
    return `${script.slice(0, insertPos)}\n\n${envBlock}${script.slice(insertPos)}`
  }
  return script
}

export function generateJenkinsfile(steps: StepData[], config: PipelineConfig = {}): string {
  const lines: string[] = []
  lines.push('pipeline {')

  if (config.agentLabel) {
    lines.push(`    agent { label '${escapeGroovy(config.agentLabel)}' }`)
  } else {
    lines.push('    agent any')
  }

  lines.push('')
  lines.push('    parameters {')
  lines.push(
    "        string(name: 'EXECUTION_ID', defaultValue: '', description: 'BuildExecution ID from TestMaster')"
  )
  lines.push('    }')

  const envMap = buildMergedEnvironmentMap(config, config.existingJenkinsfileText || '')
  lines.push('')
  lines.push(renderEnvironmentBlock(envMap))

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
    lines.push(
      `                ${formatShellCommand('echo "No build steps configured."', config.osType)}`
    )
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

      let body = formatShellCommand(script, config.osType)
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
    const reportSh = formatShellCommand(config.reportCommand, config.osType)
    lines.push('')
    lines.push('    post {')
    lines.push('        always {')
    lines.push(`            ${REPORT_UPLOAD_MARK_START}`)
    lines.push("            catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {")
    lines.push(indent(reportSh, 16))
    lines.push('            }')
    lines.push(`            ${REPORT_UPLOAD_MARK_END}`)
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
  const cleaned = content
    .replace(/\btimeout\s*\([^)]*\)\s*\{/g, '')
    .replace(/\bretry\s*\([^)]*\)\s*\{/g, '')
    .replace(/\bcatchError\s*\([^)]*\)\s*\{/g, '')
    .replace(/^\s*\}\s*$/gm, '')
  const lines = content.split('\n').filter((l) => l.trim().length > 0)
  if (!lines.length) return ''
  const minIndent = Math.min(...lines.map((l) => l.match(/^(\s*)/)![0].length))
  const normalized = lines
    .map((l) => l.slice(minIndent))
    .join('\n')
    .trim()
  if (
    normalized.startsWith('timeout(') ||
    normalized.startsWith('retry(') ||
    normalized.startsWith('catchError(')
  ) {
    const cleanedLines = cleaned.split('\n').filter((l) => l.trim().length > 0)
    if (!cleanedLines.length) return ''
    const cleanedIndent = Math.min(...cleanedLines.map((l) => l.match(/^(\s*)/)![0].length))
    return cleanedLines.map((l) => l.slice(cleanedIndent)).join('\n')
  }
  return normalized
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
  const doubleMatch = body.match(/\bsh\s+"([^"]*)"/)
  if (doubleMatch?.[1]) return unescapeGroovyDouble(doubleMatch[1])

  const batTripleStart = body.search(/\bbat\s+'''/)
  if (batTripleStart !== -1) {
    const quoteStart = body.indexOf("'''", batTripleStart)
    const content = extractTripleQuoted(body, quoteStart)
    if (content !== null) return unescapeGroovy(content)
  }
  const batSingle = body.match(/\bbat\s+'([^']*)'/)
  if (batSingle?.[1]) return unescapeGroovy(batSingle[1])
  const batDouble = body.match(/\bbat\s+"([^"]*)"/)
  if (batDouble?.[1]) return unescapeGroovyDouble(batDouble[1])
  return ''
}

function extractTripleQuoted(text: string, pos: number): string | null {
  if (text.slice(pos, pos + 3) !== "'''") return null
  let i = pos + 3
  while (i < text.length) {
    if (text[i] === '\\' && i + 1 < text.length) {
      i += 2
      continue
    }
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

function unescapeGroovyDouble(text: string): string {
  return text.replace(/\\"/g, '"').replace(/\\\\/g, '\\')
}

function extractBlock(text: string, openBracePos: number): string | null {
  if (text[openBracePos] !== '{') return null
  let depth = 0
  let i = openBracePos
  while (i < text.length) {
    const ch = text[i]
    if (ch === '\\') {
      i += 2
      continue
    }
    if (ch === "'" && text[i + 1] === "'" && text[i + 2] === "'") {
      i += 3
      while (i < text.length) {
        if (text[i] === '\\') {
          i += 2
          continue
        }
        if (text[i] === "'" && text[i + 1] === "'" && text[i + 2] === "'") {
          i += 3
          break
        }
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
