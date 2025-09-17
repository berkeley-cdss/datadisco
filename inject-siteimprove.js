const fs = require('fs');
const path = require('path');

const buildDir = path.join(__dirname, '_build', 'html');
const scriptTag = `<script src="https://siteimproveanalytics.com/js/siteanalyze_6294756.js" async></script>`;

function injectScript(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  if (!content.includes(scriptTag)) {
    content = content.replace(/<\/body>/i, `${scriptTag}\n</body>`);
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Injected script into: ${filePath}`);
  }
}

function processDir(dir) {
  for (const entry of fs.readdirSync(dir)) {
    const fullPath = path.join(dir, entry);
    if (fs.statSync(fullPath).isDirectory()) {
      processDir(fullPath);
    } else if (fullPath.endsWith('.html')) {
      injectScript(fullPath);
    }
  }
}

processDir(buildDir);
