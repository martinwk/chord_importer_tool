Here's the bare minimum to create a Firefox extension:

Steps:

    Create a folder
    Add both files above
    Open Firefox → about:debugging → "This Firefox" → "Load Temporary Add-on"
    Select the manifest.json file

That's it. The extension will log "Extension loaded!" on every page.

waar kan ik "extensionloaded lezen"?
Edit

In de Developer Console:

    Druk op F12 (of rechtermuisknop → "Inspect")
    Klik op het Console tabblad
    Refresh de pagina
    Je ziet daar: Extension loaded!

Of via menu: Tools → Web Developer → Web Console