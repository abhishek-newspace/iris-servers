const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const EMAILS_DIR = path.join(__dirname, 'emails');
const TEMP_OUT_DIR = path.join(__dirname, 'out'); // React email temp output
const KEYCLOAK_HTML_DIR = path.join(__dirname, 'my-theme-output/email/html');

console.log("🚀 1. Compiling React Emails to HTML...");
execSync(`npx email export --dir ${EMAILS_DIR} --outDir ${TEMP_OUT_DIR}`, { stdio: 'inherit' });

// Ensure Keycloak HTML directory exists
if (!fs.existsSync(KEYCLOAK_HTML_DIR)) {
  fs.mkdirSync(KEYCLOAK_HTML_DIR, { recursive: true });
}

console.log("📦 2. Converting HTML to FTL for Keycloak...");
const files = fs.readdirSync(TEMP_OUT_DIR);

files.forEach(file => {
  if (file.endsWith('.html')) {
    const oldPath = path.join(TEMP_OUT_DIR, file);
    const newFileName = file.replace('.html', '.ftl');
    const newPath = path.join(KEYCLOAK_HTML_DIR, newFileName);
    
    fs.copyFileSync(oldPath, newPath);
    console.log(`✅ Ready for Keycloak: ${newFileName}`);
  }
});

console.log("🎉 Theme successfully built in /my-theme-output");
