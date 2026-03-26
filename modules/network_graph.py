def build_graph(df, scores):
    from pyvis.network import Network

    net = Network(height='600px', width='100%', directed=True)

    # STATIC TEST GRAPH (no CSV dependency)
    net.add_node("A", label="Number A")
    net.add_node("B", label="Number B")
    net.add_node("C", label="Number C")

    net.add_edge("A", "B")
    net.add_edge("B", "C")

    net.save_graph("network.html")

    return "network.html"
