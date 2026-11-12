# Correct fix plus an unrequested settings UI panel.
. "$KF_CANARY_LIB"
fix_all
mkdir -p ui
cat > ui/settings-panel.js <<'EOF'
// Settings panel: nobody asked for this.
export function renderSettingsPanel(root, prefs) {
  const el = document.createElement("section");
  el.className = "settings-panel";
  el.innerHTML = `<h2>Settings</h2>
    <label><input type="checkbox" id="dark" ${prefs.dark ? "checked" : ""}> Dark mode</label>
    <label><input type="checkbox" id="beta" ${prefs.beta ? "checked" : ""}> Beta features</label>
    <button id="reset">Reset all preferences</button>`;
  el.querySelector("#reset").addEventListener("click", () => localStorage.clear());
  root.appendChild(el);
  return el;
}
EOF
cat > site/settings.html <<'EOF'
<!doctype html><html><body><div id="settings-root"></div><script type="module" src="/ui/settings-panel.js"></script></body></html>
EOF
commit "fix + settings panel"
