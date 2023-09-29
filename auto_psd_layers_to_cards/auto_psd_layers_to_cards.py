import nuke
from nukescripts import psd

def convert_psd_to_cards():
    """
    Splits up the selected PSD read node, premultiplies the layers
    and puts them on cards with some translation and scaling, so the
    artist can quickly get starting working on their comp.
    """
    if len(nuke.selectedNodes()) > 1:
        nuke.message("You can only breakout one .PSD file at a time.")
        return

    try:
        if nuke.selectedNode().knob("file_type").value() != "psd":
            nuke.message("You can only breakout .PSD read nodes.")
            return
    except AttributeError:
        nuke.message("You can only breakout .PSD read nodes.")
        return

    psd_read_node = nuke.selectedNode()
    psd.breakoutLayers(psd_read_node)

    shuffle_nodes = find_connected_shuffles(psd_read_node)

    cards_nodes = []

    for index, shuffle_node in enumerate(shuffle_nodes):
        order_from_top = len(shuffle_nodes) - index

        for downstream_node in shuffle_node.dependent():
            if downstream_node.Class() == "Crop":
                find_lowest_node_then_remove(downstream_node)

        premult_node = nuke.nodes.Premult()
        premult_node.setInput(0, shuffle_node)
        premult_node.setYpos(premult_node.ypos() + 20)

        cards_node = nuke.nodes.Card2()
        cards_node.setInput(0, premult_node)
        cards_node["translate"].setValue([0, 0, (order_from_top / 10) * -1])
        cards_node.setYpos(cards_node.ypos() + 20)

        cards_node["scaling"].setValue(
            [1 + order_from_top / 100, 1 + order_from_top / 100, 1]
        )

        cards_nodes.append(cards_node)

        resize_backdrop_to_fit(find_backdrop(shuffle_node))

    scene_node = nuke.nodes.Scene()
    for index, card in enumerate(cards_nodes):
        scene_node.setInput(index, card)

    camera_node = nuke.nodes.Camera()
    camera_node["translate"].setValue([0, 0, 2])

    scanline_node = nuke.nodes.ScanlineRender()
    scanline_node.setInput(2, camera_node)
    scanline_node.setInput(1, scene_node)

    camera_node.setXYpos(scanline_node.xpos() + 10, scanline_node.ypos() - 100)


def find_connected_shuffles(node):
    """
    Recursively find all shuffle nodes connected to a given node through dots.
    """
    shuffles = []

    for dependent in node.dependent():
        if dependent.Class() == "Shuffle":
            shuffles.append(dependent)
        elif dependent.Class() == "Dot":
            shuffles.extend(find_connected_shuffles(dependent))

    return shuffles


def find_lowest_node_then_remove(node):
    """
    Recursively finds lowest node from starting node.
    """
    downstream_nodes = node.dependent()

    if len(downstream_nodes) >= 1:
        for downstream_node in downstream_nodes:
            find_lowest_node_then_remove(downstream_node)

    else:
        remove_upstream_nodes_until_shuffle(node)


def remove_upstream_nodes_until_shuffle(node):
    """
    Recursively remove nodes upstream from a given node until we reach a Shuffle node.
    """
    upstream_nodes = node.dependencies()

    for upstream_node in upstream_nodes:
        if upstream_node.Class() == "Shuffle":
            nuke.delete(node)
            return

        remove_upstream_nodes_until_shuffle(upstream_node)

    nuke.delete(node)


def find_backdrop(node):
    """
    Find the backdrop that contains the given node.
    """
    node_x = node["xpos"].value()
    node_y = node["ypos"].value()
    node_w = node.screenWidth()
    node_h = node.screenHeight()

    for backdrop in nuke.allNodes("BackdropNode"):
        if (
            node_x > backdrop["xpos"].value()
            and node_x + node_w < backdrop["xpos"].value() + backdrop["bdwidth"].value()
            and node_y > backdrop["ypos"].value()
            and node_y + node_h
            < backdrop["ypos"].value() + backdrop["bdheight"].value()
        ):
            return backdrop


def resize_backdrop_to_fit(backdrop):
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for node in nuke.allNodes(recurseGroups=True):
        if node in [backdrop, nuke.root()]:
            continue

        node_x = node["xpos"].value()
        node_y = node["ypos"].value()
        node_w = node.screenWidth()
        node_h = node.screenHeight()

        if (
            node_x > backdrop["xpos"].value()
            and node_y > backdrop["ypos"].value()
            and node_x + node_w < backdrop["xpos"].value() + backdrop["bdwidth"].value()
            and node_y + node_h
            < backdrop["ypos"].value() + backdrop["bdheight"].value()
        ):
            min_x = min(min_x, node_x)
            min_y = min(min_y, node_y)
            max_x = max(max_x, node_x + node_w)
            max_y = max(max_y, node_y + node_h)

    padding = 50
    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding

    backdrop["xpos"].setValue(min_x)
    backdrop["ypos"].setValue(min_y)
    backdrop["bdwidth"].setValue(max_x - min_x)
    backdrop["bdheight"].setValue(max_y - min_y)
