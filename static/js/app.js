
const { createApp, ref, reactive, onMounted } = Vue;
const { ElMessage, ElMessageBox, ElLoading } = ElementPlus;

const app = createApp({
    setup() {
        // --- State ---
        const activeMenu = ref('testcase-manage');
        const currentView = ref('testcase-manage'); // 'interface', 'testcase', 'testcase-manage'
        const activeCollapse = ref(['schema']);
        
        // Data
        const currentInterface = ref(null);
        const currentTestCase = ref(null);
        const testCases = ref([]); // For Interface View
        const globalTestCases = ref([]); // For Manager View
        const categories = ref([]); // For Generate Dialog
        
        // Tree
        const treeRef = ref(null);
        
        // Search & Selection
        const searchKeyword = ref('');
        const multipleSelection = ref([]);

        // Dialogs
        const dialogs = reactive({
            directory: { visible: false, isEdit: false, form: { id: null, name: '', parent: null } },
            interface: { visible: false, isEdit: false, form: { id: null, name: '', method: 'GET', path: '', schemaStr: '', directory: null } },
            testcase: { visible: false, form: { id: null, name: '', test_field: '', description: '', requestDataStr: '', expectedValueStr: '' } },
            generate: { visible: false, loading: false, submitting: false, selectedIds: [] },
            export: { visible: false, format: 'json', scope: 'testcase', ids: [] }
        });

        // --- API Helper ---
        const getCookie = (name) => {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        };

        const api = {
            async request(method, url, data = null) {
                const opts = {
                    method,
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') }
                };
                if (data) opts.body = JSON.stringify(data);
                
                try {
                    const res = await fetch(`/api${url}`, opts);
                    if (!res.ok) {
                        const errData = await res.json().catch(() => ({}));
                        throw new Error(errData.detail || errData.message || `Request failed: ${res.status}`);
                    }
                    if (res.status === 204) return null;
                    return res.json();
                } catch (e) {
                    throw e;
                }
            },
            get: (url) => api.request('GET', url),
            post: (url, data) => api.request('POST', url, data),
            patch: (url, data) => api.request('PATCH', url, data),
            delete: (url, data) => api.request('DELETE', url, data)
        };

        // --- Tree Logic (Lazy Load) ---
        const loadNode = async (node, resolve) => {
            try {
                if (node.level === 0) {
                    const dirs = await api.get('/directories/');
                    // Map root directories to tree nodes
                    return resolve(dirs.map(d => ({ ...d, type: 'directory', leaf: false })));
                }
                
                if (node.data.type === 'directory') {
                    const dirId = node.data.id;
                    
                    // 1. Fetch Interfaces
                    const interfaces = await api.get(`/interfaces/?directory=${dirId}`);
                    const interfaceNodes = interfaces.map(i => ({ ...i, type: 'interface', leaf: true }));
                    
                    // 2. Subdirectories (Assuming nested structure from initial fetch or API support)
                    // If the API returns nested structure, node.data.sub_directories exists.
                    const subDirs = node.data.sub_directories || [];
                    const subDirNodes = subDirs.map(d => ({ ...d, type: 'directory', leaf: false }));
                    
                    resolve([...subDirNodes, ...interfaceNodes]);
                } else {
                    resolve([]);
                }
            } catch (e) {
                console.error(e);
                resolve([]);
            }
        };

        // --- Data Fetching ---
        const fetchInterface = async (id) => {
            const loading = ElLoading.service({ target: '.el-main', text: 'Loading...' });
            try {
                currentInterface.value = await api.get(`/interfaces/${id}/`);
                testCases.value = await api.get(`/testcases/?interface=${id}`);
                currentView.value = 'interface';
            } catch (e) { ElMessage.error(e.message); }
            finally { loading.close(); }
        };

        const fetchTestCase = async (id) => {
            const loading = ElLoading.service({ target: '.el-main' });
            try {
                currentTestCase.value = await api.get(`/testcases/${id}/`);
                currentView.value = 'testcase';
            } catch (e) { ElMessage.error(e.message); }
            finally { loading.close(); }
        };

        const fetchGlobalTestCases = async () => {
            const loading = ElLoading.service({ target: '.el-main' });
            try {
                let url = '/testcases/?';
                if (searchKeyword.value) url += `search=${encodeURIComponent(searchKeyword.value)}&`;
                globalTestCases.value = await api.get(url);
            } catch (e) { ElMessage.error(e.message); }
            finally { loading.close(); }
        };

        // --- Event Handlers ---
        const handleMenuSelect = (index) => {
            if (index === 'testcase-manage') {
                currentView.value = 'testcase-manage';
                fetchGlobalTestCases();
            }
        };

        const handleNodeClick = (data) => {
            if (data.type === 'interface') {
                fetchInterface(data.id);
            }
        };

        const handleSelectionChange = (val) => {
            multipleSelection.value = val;
        };
        
        const handleSearch = () => {
            setTimeout(fetchGlobalTestCases, 300); // Debounce
        };

        // --- Dialog Actions ---
        
        // Directory
        const openDirectoryDialog = (dir = null) => {
            if (dir) {
                dialogs.directory.isEdit = true;
                dialogs.directory.form = { id: dir.id, name: dir.name, parent: dir.parent };
            } else {
                dialogs.directory.isEdit = false;
                dialogs.directory.form = { name: '', parent: null };
            }
            dialogs.directory.visible = true;
        };

        const submitDirectory = async () => {
            try {
                if (dialogs.directory.isEdit) {
                    await api.patch(`/directories/${dialogs.directory.form.id}/`, { name: dialogs.directory.form.name });
                } else {
                    await api.post('/directories/', { name: dialogs.directory.form.name, parent: dialogs.directory.form.parent });
                }
                dialogs.directory.visible = false;
                ElMessage.success('操作成功');
                window.location.reload(); // Refresh tree
            } catch (e) { ElMessage.error(e.message); }
        };

        // Interface
        const openInterfaceDialog = (dirId = null, iface = null) => {
            if (iface) {
                dialogs.interface.isEdit = true;
                dialogs.interface.form = {
                    id: iface.id,
                    name: iface.name,
                    method: iface.method,
                    path: iface.path,
                    schemaStr: JSON.stringify(iface.schema, null, 2),
                    directory: iface.directory
                };
            } else {
                dialogs.interface.isEdit = false;
                dialogs.interface.form = {
                    name: '', method: 'GET', path: '',
                    schemaStr: '{\n  "properties": {\n    "field": {\n      "type": "string"\n    }\n  }\n}',
                    directory: dirId
                };
            }
            dialogs.interface.visible = true;
        };

        const submitInterface = async () => {
            try {
                const payload = { ...dialogs.interface.form };
                try { payload.schema = JSON.parse(payload.schemaStr); } catch (e) { return ElMessage.warning('Schema JSON Error'); }
                delete payload.schemaStr;

                if (dialogs.interface.isEdit) {
                    await api.patch(`/interfaces/${payload.id}/`, payload);
                    fetchInterface(payload.id);
                } else {
                    await api.post('/interfaces/', payload);
                    window.location.reload();
                }
                dialogs.interface.visible = false;
                ElMessage.success('操作成功');
            } catch (e) { ElMessage.error(e.message); }
        };

        // Generate
        const openGenerateDialog = async () => {
            if (!currentInterface.value) return;
            dialogs.generate.visible = true;
            dialogs.generate.loading = true;
            dialogs.generate.selectedIds = [];
            try {
                categories.value = await api.get('/categories/');
            } catch (e) { ElMessage.error(e.message); }
            finally { dialogs.generate.loading = false; }
        };

        const submitGenerate = async () => {
            if (!currentInterface.value) return;
            dialogs.generate.submitting = true;
            try {
                const res = await api.post(`/interfaces/${currentInterface.value.id}/generate_cases/`, {
                    category_ids: dialogs.generate.selectedIds
                });
                ElMessage.success(`Generated ${res.generated_count} cases`);
                dialogs.generate.visible = false;
                fetchInterface(currentInterface.value.id);
            } catch (e) { ElMessage.error(e.message); }
            finally { dialogs.generate.submitting = false; }
        };

        // Test Case
        const openTestCaseDialog = (tc) => {
            dialogs.testcase.form = {
                id: tc.id,
                name: tc.name,
                test_field: tc.test_field,
                description: tc.description,
                requestDataStr: JSON.stringify(tc.request_data, null, 2),
                expectedValueStr: JSON.stringify(tc.expected_value || tc.expected_response, null, 2)
            };
            dialogs.testcase.visible = true;
        };

        const submitTestCase = async () => {
            const payload = {
                name: dialogs.testcase.form.name,
                test_field: dialogs.testcase.form.test_field,
                description: dialogs.testcase.form.description
            };
            try {
                payload.request_data = JSON.parse(dialogs.testcase.form.requestDataStr);
                payload.expected_value = JSON.parse(dialogs.testcase.form.expectedValueStr);
            } catch (e) { return ElMessage.warning('JSON Format Error'); }

            try {
                await api.patch(`/testcases/${dialogs.testcase.form.id}/`, payload);
                ElMessage.success('Saved');
                dialogs.testcase.visible = false;
                if (currentView.value === 'interface') fetchInterface(currentInterface.value.id);
                else if (currentView.value === 'testcase') fetchTestCase(dialogs.testcase.form.id);
                else fetchGlobalTestCases();
            } catch (e) { ElMessage.error(e.message); }
        };

        const viewTestCase = (row) => {
            fetchTestCase(row.id);
        };

        const backToInterface = () => {
            if (currentInterface.value) {
                fetchInterface(currentInterface.value.id);
            } else {
                currentView.value = 'testcase-manage';
            }
        };

        const confirmDelete = (type, id) => {
            ElMessageBox.confirm('Are you sure?', 'Warning', { type: 'warning' })
                .then(async () => {
                    try {
                        const endpoint = {
                            'directory': `/directories/${id}/`,
                            'interface': `/interfaces/${id}/`,
                            'testcase': `/testcases/${id}/`
                        }[type];
                        await api.delete(endpoint);
                        ElMessage.success('Deleted');
                        
                        if (type === 'directory' || type === 'interface') window.location.reload();
                        if (type === 'testcase') {
                            if (currentView.value === 'interface') fetchInterface(currentInterface.value.id);
                            if (currentView.value === 'testcase') backToInterface();
                            if (currentView.value === 'testcase-manage') fetchGlobalTestCases();
                        }
                    } catch (e) { ElMessage.error(e.message); }
                });
        };
        
        const handleBatchDelete = () => {
            if (multipleSelection.value.length === 0) return ElMessage.warning('Select items first');
            ElMessageBox.confirm(`Delete ${multipleSelection.value.length} items?`, 'Warning', { type: 'warning' })
                .then(async () => {
                    try {
                        const ids = multipleSelection.value.map(i => i.id);
                        await api.post('/testcases/bulk_delete/', { ids });
                        ElMessage.success('Deleted');
                        if (currentView.value === 'interface') fetchInterface(currentInterface.value.id);
                        else fetchGlobalTestCases();
                    } catch(e) { ElMessage.error(e.message); }
                });
        };

        const handleBatchExport = () => {
            if (multipleSelection.value.length === 0) return ElMessage.warning('Select items first');
            dialogs.export.ids = multipleSelection.value.map(i => i.id);
            dialogs.export.visible = true;
        };

        const submitExport = async () => {
            try {
                const res = await fetch('/api/export/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ scope: 'testcase', ids: dialogs.export.ids, format: dialogs.export.format })
                });
                if (res.ok) {
                    const blob = await res.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `export.${dialogs.export.format}`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    dialogs.export.visible = false;
                    ElMessage.success('Exported');
                } else { throw new Error('Export failed'); }
            } catch(e) { ElMessage.error(e.message); }
        };

        const getMethodType = (method) => {
            const map = { GET: '', POST: 'success', PUT: 'warning', DELETE: 'danger' };
            return map[method] || 'info';
        };

        const treeProps = { label: 'name', isLeaf: 'leaf' };

        onMounted(() => {
            fetchGlobalTestCases();
        });

        return {
            activeMenu, currentView, activeCollapse, treeRef,
            currentInterface, currentTestCase, testCases, globalTestCases, categories,
            searchKeyword, multipleSelection,
            dialogs,
            // Actions
            handleMenuSelect, handleNodeClick, handleSelectionChange, handleSearch,
            openDirectoryDialog, submitDirectory,
            openInterfaceDialog, submitInterface,
            openGenerateDialog, submitGenerate,
            openTestCaseDialog, submitTestCase,
            handleBatchDelete, handleBatchExport, submitExport,
            viewTestCase, backToInterface, confirmDelete,
            getMethodType, treeProps, loadNode
        };
    }
});

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
}

app.use(ElementPlus);
app.mount('#app');
