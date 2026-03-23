<template>
  <v-container fluid>
    <!-- 页头 + 操作栏 -->
    <v-sheet class="pa-4 rounded-xl border-thin" elevation="0" color="surface">
      <v-row dense align="center" class="mb-3">
        <v-col>
          <div class="d-flex align-center">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon icon="mdi-clipboard-check-outline" size="22"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">{{ $t('testcase.title') }}</div>
              <div class="text-caption text-medium-emphasis">{{ $t('testcase.subtitle') }}</div>
            </div>
          </div>
        </v-col>
      </v-row>
      <v-row dense align="center">
        <v-col cols="12" md="3">
          <v-text-field
            v-model="search"
            :label="$t('common.search')"
            prepend-inner-icon="mdi-magnify"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
          ></v-text-field>
        </v-col>
        <v-col cols="6" md="2">
          <v-select
            v-model="filters.project"
            :items="projects"
            item-title="name"
            item-value="id"
            :label="$t('testcase.fields.project')"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
          ></v-select>
        </v-col>
        <v-col cols="6" md="2">
          <v-select
            v-model="filters.interface"
            :items="interfaces"
            item-title="name"
            item-value="id"
            :label="$t('testcase.fields.interface')"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
          ></v-select>
        </v-col>
        <v-col cols="6" md="2">
          <v-select
            v-model="filters.test_type"
            :items="testTypeItems"
            item-title="title"
            item-value="value"
            :label="$t('testcase.fields.testType')"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
          ></v-select>
        </v-col>
        <v-col cols="6" md="2">
          <v-select
            v-model="filters.strategy"
            :items="strategyItems"
            item-title="title"
            item-value="value"
            :label="$t('testcase.fields.strategy')"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            bg-color="background"
            class="rounded-lg"
          ></v-select>
        </v-col>
        <v-spacer></v-spacer>
        <v-col cols="12" md="auto" class="d-flex justify-end">
          <v-btn
            color="primary"
            prepend-icon="mdi-play-circle-outline"
            @click="handleBatchExecute"
            class="text-none"
            :loading="batchPolling"
          >
            {{ $t('testcase.actions.batchExecute') }}
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            prepend-icon="mdi-delete-outline"
            @click="handleBatchDelete()"
            class="text-none ml-2"
          >
            {{ $t('common.batchDelete') }}
          </v-btn>
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn color="secondary" variant="tonal" prepend-icon="mdi-export" v-bind="props" class="text-none ml-2">
                {{ $t('common.export') }}
              </v-btn>
            </template>
            <v-list density="compact" rounded="xl" elevation="2">
              <v-list-item @click="handleExport('excel')" :title="$t('common.exportToExcel')" prepend-icon="mdi-file-excel-outline" rounded="xl" class="mx-2 my-1"></v-list-item>
              <v-list-item @click="handleExport('xmind')" :title="$t('common.exportToXMind')" prepend-icon="mdi-brain" rounded="xl" class="mx-2 my-1"></v-list-item>
              <v-list-item @click="handleExport('json')" :title="$t('common.exportToJSON')" prepend-icon="mdi-code-json" rounded="xl" class="mx-2 my-1"></v-list-item>
            </v-list>
          </v-menu>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()" class="text-none ml-2">
            {{ $t('testcase.new') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-sheet>

    <v-card class="mt-4" elevation="1">
      <v-data-table-server
        v-model:items-per-page="pageSize"
        :headers="customHeaders"
        :items="items"
        :items-length="totalCount"
        :loading="loading"
        v-model:page="currentPage"
        fixed-header
        height="600"
        hover
        item-key="id"
        @update:options="onTableOptionsUpdate"
      >
        <!-- 自定义选择列 - 表头全选 -->
        <template v-slot:header.select>
          <v-checkbox
            v-model="isAllSelected"
            :indeterminate="selectedIds.length > 0 && selectedIds.length < items.length"
            @change="toggleSelectAll"
            hide-details
          ></v-checkbox>
        </template>
        
        <!-- 自定义选择列 - 行选择 -->
        <template v-slot:item.select="{ item }">
          <v-checkbox
            :model-value="selectedIdsSet.has(item.id)"
            @update:model-value="toggleItemSelection(item.id)"
            hide-details
          ></v-checkbox>
        </template>
        
        <template v-slot:item.project="{ item }">
          <v-chip v-if="item.project_name" size="small" label color="teal" variant="tonal">
            {{ item.project_name }}
          </v-chip>
          <span v-else class="text-grey text-caption">-</span>
        </template>

        <template v-slot:item.interface="{ item }">
          <v-chip size="small" variant="outlined" color="primary">
            {{ getInterfaceName(item.interface) }}
          </v-chip>
        </template>
        
        <template v-slot:item.category="{ item }">
          <v-chip v-if="item.category_name" size="small" label color="info">
            {{ item.category_name }}
          </v-chip>
          <span v-else class="text-grey text-caption">N/A</span>
        </template>

        <template v-slot:item.test_type="{ item }">
          <v-chip v-if="item.test_type" size="small" label :color="getTestTypeColor(item.test_type)">
            {{ getTestTypeTitle(item.test_type) }}
          </v-chip>
          <span v-else class="text-medium-emphasis">-</span>
        </template>

        <template v-slot:item.strategy="{ item }">
          <v-chip v-if="item.strategy" size="small" label color="blue">
            {{ getStrategyTitle(item.strategy) }}
          </v-chip>
          <span v-else class="text-medium-emphasis">-</span>
        </template>

        <template v-slot:item.test_field="{ item }">
          <code class="text-grey-darken-3 bg-grey-lighten-4 px-1 rounded" v-if="item.test_field">{{ item.test_field }}</code>
          <span v-else class="text-medium-emphasis">-</span>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-tooltip location="top" :text="$t('testcase.actions.execute')">
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                icon="mdi-play-circle-outline"
                variant="text"
                size="small"
                color="teal"
                @click="handleSingleExecute(item)"
              ></v-btn>
            </template>
          </v-tooltip>

          <v-tooltip location="top" :text="$t('common.detail')">
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                icon="mdi-eye"
                variant="text"
                size="small"
                color="info"
                @click="openDetailDialog(item)"
              ></v-btn>
            </template>
          </v-tooltip>

          <v-tooltip location="top" :text="$t('common.edit')">
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                icon="mdi-pencil"
                variant="text"
                size="small"
                color="primary"
                @click="openDialog(item)"
              ></v-btn>
            </template>
          </v-tooltip>

          <v-tooltip location="top" :text="$t('common.delete')">
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                icon="mdi-delete"
                variant="text"
                size="small"
                color="error"
                @click="handleDelete(item)"
              ></v-btn>
            </template>
          </v-tooltip>
        </template>

        <template v-slot:no-data>
          <v-empty-state
            icon="mdi-clipboard-text-off-outline"
            :title="$t('common.noData')"
            class="py-10"
          ></v-empty-state>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="900px" persistent>
      <v-card class="rounded-xl">
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ editedId ? $t('testcase.edit') : $t('testcase.new') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4">
          <v-form ref="form" v-model="valid">
            <v-container>
              <v-row>
                <v-col cols="12" md="8">
                  <v-text-field
                    v-model="editedItem.name"
                    :label="$t('testcase.fields.name')"
                    :rules="[v => !!v || $t('common.required')]"
                    variant="outlined"
                    density="compact"
                    required
                  ></v-text-field>
                </v-col>

        
        <v-col cols="12" md="6">
          <v-select
            v-model="editedItem.interface"
            :items="interfaces"
            item-title="name"
            item-value="id"
            :label="$t('testcase.fields.interface')"
            :rules="[v => !!v || $t('common.required')]"
            variant="outlined"
            density="compact"
            required
          ></v-select>
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="editedItem.test_field"
            :label="$t('testcase.fields.testField')"
            variant="outlined"
            density="compact"
          ></v-text-field>
        </v-col>
        
        <v-col cols="12" md="6">
          <v-select
            v-model="editedItem.test_type"
            :items="testTypeItems"
            item-title="title"
            item-value="value"
            :label="$t('testcase.fields.testType')"
            variant="outlined"
            density="compact"
            clearable
          ></v-select>
        </v-col>
        <v-col cols="12" md="6">
          <v-select
            v-model="editedItem.strategy"
            :items="strategyItems"
            item-title="title"
            item-value="value"
            :label="$t('testcase.fields.strategy')"
            variant="outlined"
            density="compact"
            clearable
          ></v-select>
        </v-col>

                <v-col cols="12">
                  <v-textarea
                    v-model="editedItem.description"
                    :label="$t('testcase.fields.description')"
                    variant="outlined"
                    rows="2"
                  ></v-textarea>
                </v-col>
                
                <v-col cols="12" md="6">
                  <v-textarea
                    v-model="editedItem._request_data_str"
                    :label="$t('testcase.fields.requestData')"
                    variant="outlined"
                    rows="8"
                    class="font-monospace"
                    hint="JSON format"
                    persistent-hint
                  ></v-textarea>
                </v-col>
                <v-col cols="12" md="6">
                  <v-textarea
                    v-model="editedItem._expected_value_str"
                    :label="$t('testcase.fields.expectedValue')"
                    variant="outlined"
                    rows="8"
                    class="font-monospace"
                    hint="JSON format"
                    persistent-hint
                  ></v-textarea>
                </v-col>
              </v-row>
            </v-container>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey-darken-1" class="text-none" @click="dialog = false">
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn color="primary" variant="flat" class="text-none ml-3" @click="save" :disabled="!valid">
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card class="rounded-xl">
        <v-toolbar color="error" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ $t('common.delete') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4 text-body-2">
          {{ deleteItemName ? $t('common.confirmDelete', { name: deleteItemName }) : '' }}
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey-darken-1" class="text-none" @click="deleteDialog = false">
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn color="error" variant="flat" class="text-none ml-3" @click="confirmDelete">
            {{ $t('common.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Batch Delete Confirmation Dialog -->
    <v-dialog v-model="batchDeleteDialog" max-width="400px">
      <v-card class="rounded-xl">
        <v-toolbar color="error" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">{{ $t('common.batchDelete') }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text class="pa-4 text-body-2">
          {{ $t('common.confirmBatchDelete', { count: selectedIds.length }) }}
        </v-card-text>
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey-darken-1" class="text-none" @click="batchDeleteDialog = false">
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn color="error" variant="flat" class="text-none ml-3" @click="confirmBatchDelete">
            {{ $t('common.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Detail Dialog -->
    <v-dialog v-model="detailDialog" max-width="960px" scrollable>
      <v-card class="rounded-xl">
        <!-- 标题栏：简洁标题 + 右上角关闭按钮 -->
        <v-toolbar color="primary" density="compact" class="px-2">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold text-white">
            {{ $t('common.detail') }}
          </v-toolbar-title>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="detailDialog = false" />
        </v-toolbar>

        <v-card-text class="pa-0" style="max-height: 75vh; overflow-y: auto;">
          <!-- 用例名称 - 独立突出显示 -->
          <div class="px-6 pt-5 pb-3">
            <div class="text-h6 font-weight-bold" style="word-break: break-word;">{{ selectedTestCase?.name }}</div>
            <div class="text-caption text-medium-emphasis mt-1">ID: {{ selectedTestCase?.id }}</div>
          </div>

          <v-divider />

          <!-- 基本信息区域 -->
          <div class="px-6 py-4">
            <v-row dense>
              <v-col cols="6" sm="4">
                <div class="detail-field">
                  <div class="detail-label">{{ $t('testcase.fields.project') }}</div>
                  <v-chip v-if="selectedTestCase?.project_name" size="small" label color="teal" variant="tonal">
                    {{ selectedTestCase.project_name }}
                  </v-chip>
                  <span v-else class="text-medium-emphasis">-</span>
                </div>
              </v-col>
              <v-col cols="6" sm="4">
                <div class="detail-field">
                  <div class="detail-label">{{ $t('testcase.fields.interface') }}</div>
                  <v-chip size="small" variant="outlined" color="primary">
                    {{ selectedTestCase?.interface ? getInterfaceName(selectedTestCase.interface) : '-' }}
                  </v-chip>
                </div>
              </v-col>
              <v-col cols="6" sm="4">
                <div class="detail-field">
                  <div class="detail-label">{{ $t('testcase.fields.testType') }}</div>
                  <v-chip v-if="selectedTestCase?.test_type" size="small" label :color="getTestTypeColor(selectedTestCase.test_type)">
                    {{ getTestTypeTitle(selectedTestCase.test_type) }}
                  </v-chip>
                  <span v-else class="text-medium-emphasis">-</span>
                </div>
              </v-col>
              <v-col cols="6" sm="4">
                <div class="detail-field">
                  <div class="detail-label">{{ $t('testcase.fields.strategy') }}</div>
                  <v-chip v-if="selectedTestCase?.strategy" size="small" label color="blue">
                    {{ getStrategyTitle(selectedTestCase.strategy) }}
                  </v-chip>
                  <span v-else class="text-medium-emphasis">-</span>
                </div>
              </v-col>
              <v-col cols="6" sm="4">
                <div class="detail-field">
                  <div class="detail-label">{{ $t('testcase.fields.category') }}</div>
                  <div class="detail-value">{{ selectedTestCase?.category_name || '-' }}</div>
                </div>
              </v-col>
              <v-col cols="6" sm="4">
                <div class="detail-field">
                  <div class="detail-label">{{ $t('testcase.fields.testField') }}</div>
                  <code v-if="selectedTestCase?.test_field" class="text-body-2">{{ selectedTestCase.test_field }}</code>
                  <span v-else class="text-medium-emphasis">-</span>
                </div>
              </v-col>
              <v-col cols="6" sm="4">
                <div class="detail-field">
                  <div class="detail-label">{{ $t('testcase.fields.createdAt') }}</div>
                  <div class="detail-value">{{ selectedTestCase?.created_at || '-' }}</div>
                </div>
              </v-col>
            </v-row>
          </div>

          <!-- 描述 -->
          <template v-if="selectedTestCase?.description">
            <v-divider />
            <div class="px-6 py-4">
              <div class="detail-label mb-2">{{ $t('testcase.fields.description') }}</div>
              <div class="text-body-2" style="word-break: break-word; white-space: pre-wrap;">{{ selectedTestCase.description }}</div>
            </div>
          </template>

          <v-divider />

          <!-- 请求数据 & 期望值 - 全宽展示避免溢出 -->
          <div class="px-6 py-4">
            <v-row>
              <v-col cols="12" md="6">
                <div class="detail-label mb-2">{{ $t('testcase.fields.requestData') }}</div>
                <pre class="detail-json-block">{{ selectedTestCase?.request_data ? JSON.stringify(selectedTestCase.request_data, null, 2) : '{}' }}</pre>
              </v-col>
              <v-col cols="12" md="6">
                <div class="detail-label mb-2">{{ $t('testcase.fields.expectedValue') }}</div>
                <pre class="detail-json-block">{{ selectedTestCase?.expected_value ? JSON.stringify(selectedTestCase.expected_value, null, 2) : '{}' }}</pre>
              </v-col>
            </v-row>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Execution Result Drawer -->
    <v-navigation-drawer
      v-model="execDrawer"
      location="right"
      temporary
      :width="540"
      class="exec-drawer"
    >
      <v-toolbar color="teal" density="compact" class="px-2">
        <v-icon class="mr-2">mdi-play-circle</v-icon>
        <v-toolbar-title class="text-subtitle-2 font-weight-bold text-white">
          {{ execDrawerMode === 'single' ? execCaseName : $t('testcase.drawer.batchProgress') }}
        </v-toolbar-title>
        <v-spacer />
        <v-chip v-if="execResult && !execLoading" :color="execStatusColor(execResult.status)" size="small" variant="flat" class="mr-2">
          {{ $t(`execution.status.${execResult.status}`, execResult.status) }}
        </v-chip>
        <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="execDrawer = false" />
      </v-toolbar>

      <div class="pa-4" style="height: calc(100% - 48px); overflow-y: auto;">
        <!-- Loading State -->
        <div v-if="execLoading" class="d-flex flex-column align-center justify-center" style="height: 300px;">
          <v-progress-circular indeterminate color="teal" size="48" />
          <div class="text-body-2 text-medium-emphasis mt-4">{{ $t('testcase.drawer.executing') }}</div>
          <div class="text-caption text-disabled mt-1">{{ $t('testcase.drawer.executingHint') }}</div>
        </div>

        <!-- Single Result -->
        <template v-else-if="execDrawerMode === 'single' && execResult">
          <v-row dense class="mb-3">
            <v-col cols="auto">
              <div class="text-caption text-medium-emphasis">{{ $t('execution.detail.statusCode') }}</div>
              <v-chip :color="execResult.response_status >= 400 ? 'error' : 'success'" size="small" variant="flat">
                {{ execResult.response_status ?? '-' }}
              </v-chip>
            </v-col>
            <v-col cols="auto">
              <div class="text-caption text-medium-emphasis">{{ $t('execution.detail.responseTime') }}</div>
              <span class="text-body-2 font-weight-medium">{{ execResult.response_time_ms ?? '-' }}ms</span>
            </v-col>
            <v-col cols="auto">
              <div class="text-caption text-medium-emphasis">{{ $t('execution.headers.assertions') }}</div>
              <span class="text-success">{{ execResult.assertions_passed ?? 0 }}</span>
              <span class="text-medium-emphasis mx-1">/</span>
              <span :class="(execResult.assertions_failed ?? 0) > 0 ? 'text-error' : 'text-medium-emphasis'">{{ execResult.assertions_failed ?? 0 }}</span>
            </v-col>
          </v-row>

          <v-tabs v-model="execTab" density="compact" bg-color="transparent" class="border-b mb-3">
            <v-tab value="request">{{ $t('execution.tabs.request') }}</v-tab>
            <v-tab value="response">{{ $t('execution.tabs.response') }}</v-tab>
            <v-tab value="assertions">{{ $t('execution.tabs.assertions') }}</v-tab>
            <v-tab v-if="execResult.error_message" value="error">{{ $t('execution.tabs.error') }}</v-tab>
          </v-tabs>

          <v-window v-model="execTab">
            <v-window-item value="request">
              <div class="d-flex align-center mb-2">
                <v-chip :color="drawerMethodColor(execResult.request_method)" variant="flat" label size="x-small" class="font-weight-bold mr-2">
                  {{ execResult.request_method }}
                </v-chip>
                <code class="text-caption" style="word-break: break-all;">{{ execResult.request_url }}</code>
              </div>
              <div class="text-caption font-weight-medium mb-1">{{ $t('execution.detail.requestHeaders') }}</div>
              <pre class="drawer-json">{{ drawerFormatJson(execResult.request_headers) }}</pre>
              <div class="text-caption font-weight-medium mt-2 mb-1">{{ $t('execution.detail.requestBody') }}</div>
              <pre class="drawer-json">{{ drawerFormatJson(execResult.request_body) }}</pre>
            </v-window-item>

            <v-window-item value="response">
              <div class="text-caption font-weight-medium mb-1">{{ $t('execution.detail.responseHeaders') }}</div>
              <pre class="drawer-json">{{ drawerFormatJson(execResult.response_headers) }}</pre>
              <div class="text-caption font-weight-medium mt-2 mb-1">{{ $t('execution.detail.responseBody') }}</div>
              <pre class="drawer-json">{{ drawerFormatJson(execResult.response_body) }}</pre>
            </v-window-item>

            <v-window-item value="assertions">
              <v-list v-if="execResult.assertion_details?.length" density="compact" lines="two">
                <v-list-item
                  v-for="(a, idx) in execResult.assertion_details"
                  :key="idx"
                  :prepend-icon="a.passed ? 'mdi-check-circle' : 'mdi-alert-circle'"
                  :base-color="a.passed ? 'success' : 'error'"
                >
                  <v-list-item-title class="text-body-2">{{ a.message }}</v-list-item-title>
                  <v-list-item-subtitle v-if="a.description" class="text-caption">{{ a.description }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
              <div v-else class="text-center text-medium-emphasis py-6">
                <v-icon size="32" class="mb-2">mdi-check-all</v-icon>
                <div class="text-caption">No assertions</div>
              </div>
            </v-window-item>

            <v-window-item v-if="execResult.error_message" value="error">
              <v-alert type="error" density="compact" class="mb-2">{{ execResult.error_message }}</v-alert>
              <pre v-if="execResult.error_traceback" class="drawer-json">{{ execResult.error_traceback }}</pre>
            </v-window-item>
          </v-window>
        </template>

        <!-- Batch Result -->
        <template v-else-if="execDrawerMode === 'batch' && batchResult">
          <!-- Progress -->
          <div class="mb-3">
            <div class="d-flex justify-space-between align-center mb-1">
              <span class="text-body-2 font-weight-medium">
                {{ batchCompletedCount }} / {{ batchResult.total_cases }}
              </span>
              <v-chip
                :color="batchResult.status === 'completed' ? 'success' : batchResult.status === 'running' ? 'info' : 'grey'"
                size="x-small" variant="flat"
              >
                {{ $t(`execution.batchStatus.${batchResult.status}`, batchResult.status) }}
              </v-chip>
            </div>
            <v-progress-linear
              :model-value="batchResult.total_cases > 0 ? (batchCompletedCount / batchResult.total_cases) * 100 : 0"
              :indeterminate="batchResult.status === 'pending'"
              color="teal"
              height="6"
              rounded
            />
          </div>

          <v-row dense class="mb-3">
            <v-col cols="4">
              <v-card variant="tonal" color="success" class="rounded-lg">
                <v-card-text class="text-center py-2">
                  <div class="text-h6">{{ batchResult.passed_cases }}</div>
                  <div class="text-caption">{{ $t('execution.stats.passed') }}</div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="4">
              <v-card variant="tonal" color="error" class="rounded-lg">
                <v-card-text class="text-center py-2">
                  <div class="text-h6">{{ batchResult.failed_cases }}</div>
                  <div class="text-caption">{{ $t('execution.stats.failed') }}</div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="4">
              <v-card variant="tonal" color="warning" class="rounded-lg">
                <v-card-text class="text-center py-2">
                  <div class="text-h6">{{ batchResult.error_cases }}</div>
                  <div class="text-caption">{{ $t('execution.stats.error') }}</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <v-list v-if="batchResult.execution_records?.length" density="compact" lines="two">
            <v-list-item
              v-for="rec in batchResult.execution_records"
              :key="rec.id"
              :prepend-icon="rec.status === 'passed' ? 'mdi-check-circle' : rec.status === 'failed' ? 'mdi-close-circle' : 'mdi-alert-circle'"
              :base-color="execStatusColor(rec.status)"
              @click="openBatchRecordDetail(rec)"
              class="rounded-lg mb-1"
            >
              <v-list-item-title class="text-body-2">{{ rec.test_case_name }}</v-list-item-title>
              <v-list-item-subtitle class="text-caption">
                {{ rec.request_method }} {{ rec.request_url }} · {{ rec.response_time_ms ?? '-' }}ms
              </v-list-item-subtitle>
              <template #append>
                <v-chip :color="execStatusColor(rec.status)" size="x-small" variant="flat">
                  {{ $t(`execution.status.${rec.status}`, rec.status) }}
                </v-chip>
              </template>
            </v-list-item>
          </v-list>
        </template>

        <!-- Footer -->
        <div v-if="!execLoading" class="mt-4 pt-3 border-t d-flex justify-space-between align-center">
          <v-btn
            variant="text"
            color="primary"
            size="small"
            prepend-icon="mdi-history"
            class="text-none"
            @click="goToHistory"
          >
            {{ $t('testcase.drawer.viewHistory') }}
          </v-btn>
          <v-btn variant="tonal" size="small" class="text-none" @click="execDrawer = false">
            {{ $t('common.close') }}
          </v-btn>
        </div>
      </div>
    </v-navigation-drawer>

    <v-snackbar v-model="snackbar" :color="snackbarColor" location="top right">
      {{ snackbarText }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { getTestCasesPaginated, createTestCase, updateTestCase, deleteTestCase, exportTestCases, batchDeleteTestCases } from '@/api/testcase'
import { getInterfaces } from '@/api/interface'
import { getDirectories } from '@/api/directory'
import { getCategories } from '@/api/category'
import { executeSingleCase, executeTestCases, getBatchDetail } from '@/api/execution'
import type { TestCase } from '@/api/testcase'
import type { Interface } from '@/api/interface'
import type { Directory } from '@/api/directory'
import type { TestCaseCategory } from '@/api/category'

const { t } = useI18n()
const router = useRouter()

const loading = ref(false)
const dialog = ref(false)
const detailDialog = ref(false)
const valid = ref(false)
const items = ref<TestCase[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const sortBy = ref<{ key: string; order: string }[]>([])
const interfaces = ref<Interface[]>([])
const projects = ref<Directory[]>([])
const categories = ref<TestCaseCategory[]>([])
const editedId = ref<number | null>(null)
const deleteDialog = ref(false)
const batchDeleteDialog = ref(false)
const deleteItemId = ref<number | null>(null)
const deleteItemName = ref('')
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')
const search = ref('')
const selectedTestCase = ref<TestCase | null>(null)
const filters = ref({
  project: null as number | null,
  interface: null as number | null,
  test_type: null as string | null,
  strategy: null as string | null
})

// Execution drawer state
const execDrawer = ref(false)
const execDrawerMode = ref<'single' | 'batch'>('single')
const execLoading = ref(false)
const execResult = ref<any>(null)
const execCaseName = ref('')
const execTab = ref('request')
const batchResult = ref<any>(null)
const batchPolling = ref(false)
let pollTimerId: ReturnType<typeof setTimeout> | null = null

const batchCompletedCount = computed(() => {
  if (!batchResult.value) return 0
  return (batchResult.value.passed_cases || 0) + (batchResult.value.failed_cases || 0) + (batchResult.value.error_cases || 0)
})

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

const testTypeItems = computed(() => [
  { value: 'positive', title: t('testcase.testType.positive') },
  { value: 'negative', title: t('testcase.testType.negative') },
  { value: 'boundary', title: t('testcase.testType.boundary') },
  { value: 'security', title: t('testcase.testType.security') },
])

const strategyItems = ref<{ value: string; title: string }[]>([])

// 扩展 TestCase 类型以支持前端临时字段
interface TestCaseForm extends Partial<TestCase> {
  _request_data_str?: string
  _expected_value_str?: string
}

const defaultItem: TestCaseForm = {
  name: '',
  description: '',
  test_field: '',
  interface: undefined,
  test_type: undefined,
  _request_data_str: '{}',
  _expected_value_str: '{}'
}

const editedItem = ref<TestCaseForm>({ ...defaultItem })

// 创建自定义表头，添加选择列
const customHeaders = computed(() => [
  { title: '', key: 'select', sortable: false, width: '50px', align: 'center' as const },
  { title: t('testcase.fields.id'), key: 'id', align: 'start' as const },
  { title: t('testcase.fields.name'), key: 'name', minWidth: '260px' },
  { title: t('testcase.fields.project'), key: 'project' },
  { title: t('testcase.fields.interface'), key: 'interface' },
  { title: t('testcase.fields.testType'), key: 'test_type' },
  { title: t('testcase.fields.strategy'), key: 'strategy' },
  { title: t('testcase.fields.testField'), key: 'test_field' },
  { title: t('common.actions'), key: 'actions', sortable: false, align: 'end' as const },
])

// 使用Set存储选中的ID，避免重复
const selectedIdsSet = ref(new Set<number>())

// 计算属性：获取选中的ID数组
const selectedIds = computed(() => Array.from(selectedIdsSet.value))

// 计算属性：获取选中的项目数组
const selectedItems = computed(() => {
  return items.value.filter(item => selectedIdsSet.value.has(item.id))
})

// 切换单个项目的选择状态
const toggleItemSelection = (id: number) => {
  if (selectedIdsSet.value.has(id)) {
    selectedIdsSet.value.delete(id)
  } else {
    selectedIdsSet.value.add(id)
  }
}

// 切换全选状态（当前页）
const toggleSelectAll = () => {
  if (selectedIds.value.length === items.value.length) {
    selectedIdsSet.value.clear()
  } else {
    selectedIdsSet.value = new Set(items.value.map(item => item.id))
  }
}

// 检查是否全选（当前页）
const isAllSelected = computed(() => {
  return items.value.length > 0 && selectedIds.value.length === items.value.length
})

// 保存所有类别数据，用于后续查找
const allCategories = ref<any[]>([])

// 递归获取所有子类别
const getAllSubCategories = (categories: any[]): any[] => {
  let allSubCategories: any[] = []
  
  const flattenCategories = (cats: any[]) => {
    cats.forEach(cat => {
      if (cat.sub_categories && cat.sub_categories.length > 0) {
        cat.sub_categories.forEach((subCat: any) => {
          allSubCategories.push({
            value: subCat.code,
            title: subCat.name
          })
        })
        flattenCategories(cat.sub_categories)
      }
    })
  }
  
  flattenCategories(categories)
  return allSubCategories
}

// 从所有类别中查找category_name对应的策略代码
const getStrategyCodeFromCategoryName = (categoryName: string): string | undefined => {
  let strategyCode: string | undefined
  
  const findCategory = (categories: any[]) => {
    for (const cat of categories) {
      if (cat.sub_categories && cat.sub_categories.length > 0) {
        for (const subCat of cat.sub_categories) {
          if (subCat.name === categoryName) {
            strategyCode = subCat.code
            return
          }
          if (subCat.sub_categories && subCat.sub_categories.length > 0) {
            findCategory(subCat.sub_categories)
          }
        }
      }
    }
  }
  
  findCategory(allCategories.value)
  return strategyCode
}

// v-data-table-server 的 options 变更处理
const onTableOptionsUpdate = (options: any) => {
  currentPage.value = options.page
  pageSize.value = options.itemsPerPage
  if (options.sortBy && options.sortBy.length > 0) {
    sortBy.value = options.sortBy
  } else {
    sortBy.value = []
  }
  loadTestCases()
}

// 搜索和筛选条件变更时重置到第一页并刷新
// 如果 page 从 N→1 变化，v-data-table-server 会自动触发 update:options → loadTestCases
// 如果 page 已经是 1，prop 无变化，需要手动触发
watch([() => filters.value.project, () => filters.value.interface, () => filters.value.test_type, () => filters.value.strategy], () => {
  if (currentPage.value !== 1) {
    currentPage.value = 1
  } else {
    loadTestCases()
  }
})

watch(search, () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    if (currentPage.value !== 1) {
      currentPage.value = 1
    } else {
      loadTestCases()
    }
  }, 400)
})

// 加载测试用例（服务端分页）
const loadTestCases = async () => {
  loading.value = true
  try {
    // 构建排序参数
    let ordering = '-updated_at'
    if (sortBy.value.length > 0) {
      const sort = sortBy.value[0]
      ordering = sort.order === 'desc' ? `-${sort.key}` : sort.key
    }

    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
      ordering,
    }
    if (search.value) params.search = search.value
    if (filters.value.project) params.project = filters.value.project
    if (filters.value.interface) params.interface = filters.value.interface
    if (filters.value.test_type) params.test_type = filters.value.test_type

    const response = await getTestCasesPaginated(params)

    // 映射 category_name -> strategy
    const processedTestCases = response.results.map(testCase => {
      const copy = { ...testCase }
      if (copy.category_name && !copy.strategy) {
        const strategyCode = getStrategyCodeFromCategoryName(copy.category_name)
        if (strategyCode) copy.strategy = strategyCode
      }
      return copy
    })

    items.value = processedTestCases
    totalCount.value = response.count
  } catch (error) {
    showMsg(t('common.error'), 'error')
  } finally {
    loading.value = false
  }
}

// 加载辅助数据（接口列表 + 分类列表）
const loadMetadata = async () => {
  try {
    const [interfacesData, directoriesData, categoriesData] = await Promise.all([
      getInterfaces({ no_page: true }),
      getDirectories(),
      getCategories()
    ])
    interfaces.value = interfacesData
    projects.value = directoriesData
    categories.value = categoriesData
    allCategories.value = categoriesData
    strategyItems.value = getAllSubCategories(categoriesData)
  } catch (error) {
    console.error(error)
  }
}

const loadData = async () => {
  await loadMetadata()
  // loadTestCases 由 v-data-table-server 的 @update:options 自动触发
}

const getInterfaceName = (id: number) => {
  const iface = interfaces.value.find(i => i.id === id)
  return iface ? iface.name : id
}

const getTestTypeTitle = (type: string) => {
  return t(`testcase.testType.${type}`, type)
}

const getTestTypeColor = (type: string) => {
  const map: Record<string, string> = {
    positive: 'green',
    negative: 'red',
    boundary: 'orange',
    security: 'purple'
  }
  return map[type] || 'grey'
}

const getStrategyTitle = (strategy: string) => {
  // 从strategyItems中查找对应的title
  const strategyItem = strategyItems.value.find(item => item.value === strategy)
  return strategyItem ? strategyItem.title : strategy
}

const openDialog = (item?: TestCase) => {
  if (item) {
    editedId.value = item.id
    const tempItem = { 
      ...item,
      _request_data_str: JSON.stringify(item.request_data || {}, null, 2),
      _expected_value_str: JSON.stringify(item.expected_value || {}, null, 2)
    }
    
    // 如果有category_name字段，将其转换为对应的strategy代码
    if (item.category_name) {
      // 使用getStrategyCodeFromCategoryName函数查找匹配的策略代码
      const strategyCode = getStrategyCodeFromCategoryName(item.category_name)
      if (strategyCode) {
        tempItem.strategy = strategyCode
      }
    }
    
    editedItem.value = tempItem
  } else {
    editedId.value = null
    editedItem.value = { ...defaultItem }
    if (interfaces.value.length > 0 && interfaces.value[0]) {
      editedItem.value.interface = interfaces.value[0].id
    }
  }
  dialog.value = true
}

const openDetailDialog = (item: TestCase) => {
  selectedTestCase.value = item
  detailDialog.value = true
}

const save = async () => {
  try {
    // 转换 JSON 字符串
    const payload: Partial<TestCase> = {
      ...editedItem.value,
      request_data: JSON.parse(editedItem.value._request_data_str || '{}'),
      expected_value: JSON.parse(editedItem.value._expected_value_str || '{}')
    }
    // 删除前端临时字段
    delete (payload as any)._request_data_str
    delete (payload as any)._expected_value_str

    if (editedId.value) {
      await updateTestCase(editedId.value, payload)
      showMsg(t('common.success'))
    } else {
      await createTestCase(payload)
      showMsg(t('common.success'))
    }
    dialog.value = false
    loadTestCases()
  } catch (error) {
    if (error instanceof SyntaxError) {
      showMsg('Invalid JSON format', 'error')
    } else {
      showMsg(t('common.error'), 'error')
    }
  }
}

const handleDelete = (item: TestCase) => {
  deleteItemId.value = item.id
  deleteItemName.value = item.name
  deleteDialog.value = true
}

const confirmDelete = async () => {
  if (deleteItemId.value) {
    try {
      await deleteTestCase(deleteItemId.value)
      showMsg(t('common.success'))
      loadTestCases()
    } catch (error) {
      showMsg(t('common.error'), 'error')
    } finally {
      deleteDialog.value = false
    }
  }
}

const handleBatchDelete = () => {
  if (selectedIds.value.length > 0) {
    batchDeleteDialog.value = true
  } else {
    showMsg(t('common.noSelectedItems'), 'warning')
  }
}

const confirmBatchDelete = async () => {
  if (selectedIds.value.length > 0) {
    try {
      await batchDeleteTestCases(selectedIds.value)
      showMsg(t('common.success'))
      loadTestCases()
      // 清空选中状态 - 直接清空Set
      selectedIdsSet.value.clear()
    } catch (error) {
      showMsg(t('common.error'), 'error')
    } finally {
      batchDeleteDialog.value = false
    }
  }
}

const handleExport = async (format: 'excel' | 'xmind' | 'json') => {
  try {
    // 优先使用用户选择的ID，如果没有选择则使用当前页的ID
    const ids = selectedIds.value.length > 0 
      ? selectedIds.value
      : items.value.map(item => item.id)
    
    if (ids.length === 0) {
      showMsg(t('common.noDataToExport'), 'warning')
      return
    }
    
    const blob = await exportTestCases(format, ids)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `test_cases.${format === 'excel' ? 'xlsx' : format}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    showMsg(t('common.success'))
  } catch (error) {
    showMsg(t('common.error'), 'error')
  }
}

const showMsg = (text: string, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// --- Execution handlers ---

const handleSingleExecute = async (item: TestCase) => {
  execDrawerMode.value = 'single'
  execCaseName.value = item.name
  execResult.value = null
  execTab.value = 'request'
  execLoading.value = true
  execDrawer.value = true

  try {
    const res = await executeSingleCase({ case_id: item.id })
    execResult.value = (res as any).result || res
  } catch (e: any) {
    const msg = e?.response?.data?.error || e?.message || t('common.error')
    showMsg(msg, 'error')
    execResult.value = { status: 'error', error_message: msg, request_method: '', request_url: '', request_headers: {}, request_body: {}, response_headers: {}, response_body: {}, assertion_details: [] }
  } finally {
    execLoading.value = false
  }
}

const stopPolling = () => {
  if (pollTimerId) {
    clearTimeout(pollTimerId)
    pollTimerId = null
  }
  batchPolling.value = false
}

const handleBatchExecute = async () => {
  if (selectedIds.value.length === 0) {
    showMsg(t('common.noSelectedItems'), 'warning')
    return
  }

  stopPolling()
  execDrawerMode.value = 'batch'
  batchResult.value = null
  execLoading.value = true
  execDrawer.value = true
  batchPolling.value = true

  try {
    const res = await executeTestCases({
      name: `Batch-${new Date().toLocaleString()}`,
      case_ids: selectedIds.value,
    })
    const batchDbId = (res as any).batch_db_id
    execLoading.value = false
    pollBatch(batchDbId)
  } catch (e: any) {
    const msg = e?.response?.data?.error || e?.message || t('common.error')
    showMsg(msg, 'error')
    execLoading.value = false
    batchPolling.value = false
  }
}

const pollBatch = async (batchId: number) => {
  const doPoll = async () => {
    if (!batchPolling.value) return
    try {
      const batch = await getBatchDetail(batchId)
      batchResult.value = batch
      if ((batch as any).status === 'completed' || (batch as any).status === 'cancelled') {
        batchPolling.value = false
        pollTimerId = null
      } else {
        pollTimerId = setTimeout(doPoll, 1000)
      }
    } catch {
      batchPolling.value = false
      pollTimerId = null
    }
  }
  doPoll()
}

watch(execDrawer, (open) => {
  if (!open) stopPolling()
})

const openBatchRecordDetail = (rec: any) => {
  execDrawerMode.value = 'single'
  execCaseName.value = rec.test_case_name
  execResult.value = rec
  execTab.value = 'request'
}

const goToHistory = () => {
  const query: Record<string, string> = {}
  if (filters.value.project) query.project = String(filters.value.project)
  if (filters.value.interface) query.interface = String(filters.value.interface)
  router.push({ name: 'ExecutionRecords', query })
}

const execStatusColor = (s: string) => {
  const m: Record<string, string> = { passed: 'success', failed: 'error', error: 'warning', pending: 'grey', running: 'info' }
  return m[s] || 'grey'
}

const drawerMethodColor = (m: string) => {
  const c: Record<string, string> = { GET: 'green', POST: 'blue', PUT: 'orange', DELETE: 'red', PATCH: 'purple' }
  return c[m] || 'grey'
}

const drawerFormatJson = (obj: any) => {
  if (!obj) return '{}'
  try { return typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.font-monospace :deep(textarea) {
  font-family: monospace;
}
:deep(.v-data-table td) {
  white-space: normal !important;
  word-break: break-word;
}
.drawer-json {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 10px 14px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre;
  max-height: 240px;
  overflow-y: auto;
  margin: 0;
}

.detail-field {
  margin-bottom: 12px;
}
.detail-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 4px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.detail-value {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.87);
}
.detail-json-block {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 12px 16px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8125rem;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  word-break: normal;
  max-height: 320px;
  overflow-y: auto;
  margin: 0;
}
</style>
