const { app, BrowserWindow } = require('electron');
const { exec } = require('child_process');
const path = require('path');

let streamlitProcess;

function createWindow() {
  const win = new BrowserWindow({
    width: 600,
    height: 800,
  });

  // Wait a few seconds for Streamlit to start
  setTimeout(() => {
    win.loadURL('http://localhost:8501');
  }, 5000);

  win.on('closed', () => {
    if (streamlitProcess) streamlitProcess.kill();
    app.quit();
  });
}

app.whenReady().then(() => {
  // Run Streamlit in headless mode (no browser)
  streamlitProcess = exec(
    'streamlit run chore_tracker.py --server.headless true --server.port 8501',
    { cwd: __dirname }
  );

  // Optional: log Streamlit output
  streamlitProcess.stdout.on('data', data => console.log(data.toString()));
  streamlitProcess.stderr.on('data', data => console.error(data.toString()));

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
