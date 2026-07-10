const { app, BrowserWindow, dialog } = require('electron');
const path   = require('path');
const { spawn } = require('child_process');
const http   = require('http');
const fs     = require('fs');

let mainWindow     = null;
let backendProcess = null;
const PORT = 5000;

// ── Trouver le bon chemin selon prod ou dev ──────────────────────
function getBackendDir() {
  if (app.isPackaged) {
    // En prod : les ressources sont dans resources/
    return path.join(process.resourcesPath, 'backend');
  }
  // En dev : remonter au dossier racine du projet
  return path.join(__dirname, '..');
}

function getFrontendDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'frontend');
  }
  return null; // En dev on charge Vite
}

// ── Lancer Flask ─────────────────────────────────────────────────
function startBackend() {
  const backendDir = getBackendDir();

  if (app.isPackaged) {
    // Production : lancer l'exe PyInstaller
    const isWin  = process.platform === 'win32';
    const exeName = isWin ? 'backend_app.exe' : 'backend_app';
    const exePath = path.join(backendDir, exeName);

    if (!fs.existsSync(exePath)) {
      dialog.showErrorBox('Erreur', `Backend introuvable :\n${exePath}`);
      app.quit();
      return;
    }

    backendProcess = spawn(exePath, [], {
      cwd: backendDir,
      stdio: 'pipe',
      env: { ...process.env, FLASK_ENV: 'production' },
    });
  } else {
    // Développement : lancer main.py avec python
    const pyCmd  = process.platform === 'win32' ? 'python' : 'python3';
    const script = path.join(backendDir, 'main.py');

    backendProcess = spawn(pyCmd, [script], {
      cwd: backendDir,
      stdio: 'pipe',
    });
  }

  backendProcess.stdout?.on('data', d => console.log('[Flask]', d.toString().trim()));
  backendProcess.stderr?.on('data', d => console.error('[Flask ERR]', d.toString().trim()));
  backendProcess.on('error', err => {
    dialog.showErrorBox('Erreur backend', `Impossible de lancer Flask :\n${err.message}`);
  });
}

// ── Attendre que Flask réponde ───────────────────────────────────
function waitForFlask(maxWaitMs = 15000, intervalMs = 300) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      http.get(`http://127.0.0.1:${PORT}/api/comptes`, res => {
        resolve();
      }).on('error', () => {
        if (Date.now() - start > maxWaitMs) {
          reject(new Error(`Flask non disponible après ${maxWaitMs / 1000}s`));
        } else {
          setTimeout(check, intervalMs);
        }
      });
    };
    check();
  });
}

// ── Fenêtre principale ───────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width:    1280,
    height:   800,
    minWidth:  900,
    minHeight: 600,
    title: 'Mes Comptes',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration:  false,
      contextIsolation: true,
    },
    show: false, // on affiche quand prêt
  });

  if (app.isPackaged) {
    // Prod : index.html buildé par Vite
    mainWindow.loadFile(path.join(getFrontendDir(), 'index.html'));
  } else {
    // Dev : serveur Vite
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  }

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
}

// ── Cycle de vie ─────────────────────────────────────────────────
app.whenReady().then(async () => {
  startBackend();
  try {
    await waitForFlask();
    createWindow();
  } catch (err) {
    dialog.showErrorBox('Erreur de démarrage', err.message);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) createWindow();
});

app.on('before-quit', stopBackend);

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}
