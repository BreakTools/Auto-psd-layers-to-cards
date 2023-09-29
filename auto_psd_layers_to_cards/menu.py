menubar = nuke.menu("Nuke")
edit_menu = menubar.addMenu("&Edit")
edit_menu.addCommand("-", "", "")
edit_menu.addCommand(
    "Breakout .PSD to 3d cards",
    "import auto_psd_layers_to_cards;auto_psd_layers_to_cards.convert_psd_to_cards()",
)
