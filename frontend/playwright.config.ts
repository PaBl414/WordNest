import {defineConfig,devices} from '@playwright/test';
import path from 'node:path';
import {existsSync} from 'node:fs';
const venvPython=path.resolve('..','.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
const python=process.env.WORDNEST_PYTHON||(existsSync(venvPython)?venvPython:(process.platform==='win32'?'python':'python3'));
export default defineConfig({
 testDir:'./e2e',fullyParallel:false,workers:1,
 use:{baseURL:'http://127.0.0.1:8010',trace:'retain-on-failure'},
 projects:[{name:'desktop',use:{...devices['Desktop Chrome']}},{name:'mobile',use:{...devices['Pixel 7']}}],
 webServer:{command:`"${python}" ../start.py --port 8010`,url:'http://127.0.0.1:8010/api/v1/config',reuseExistingServer:false,env:{WORDNEST_DATA:path.resolve('..','work','e2e-data')},timeout:30000}
});
