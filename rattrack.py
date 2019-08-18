#!/usr/bin/python3

from tkinter import *
import subprocess
import xml.etree.ElementTree
import os
import platform

FOREGROUND_COLOR="#686868"

def mangle_path(s):
    if platform.system() == "Windows":
        return s.replace("/", "\\")
    return s

if platform.system() == "Windows":
    os.environ["PATH"] += os.pathsep + mangle_path(os.path.dirname(os.path.realpath(__file__)) + "/windows/graphviz")
sys.path.insert(0, mangle_path(os.path.dirname(os.path.realpath(__file__)) + "/python/site-packages"))

import pydot

def graph_reduce(graph, roots, filename):
    r = list(roots)
    text_file = open(filename, "wb")
    text_file.write(graph.create_dot())
    text_file.close()

    (g,)=pydot.graph_from_dot_file(filename)
    g.set("rankdir", "LR")
    g.set("bgcolor", "#181818")
    gdict = { n.get_name() : [] for n in g.get_node_list() }

    for edge in g.get_edge_list():
        source = edge.get_source()
        dest   = edge.get_destination()
        gdict[source].append(dest)
        gdict[dest].append(source)

    def addRoots(l):
        for root in l:
            if not root in r:
                r.append(root)
                addRoots(gdict[root])

    for root in roots:
        addRoots(gdict[root])

    for edge in g.get_edge_list():
        if edge.get("color") is None:
            edge.set("color", FOREGROUND_COLOR)
        if edge.get("fontcolor") is None:
            edge.set("fontcolor", FOREGROUND_COLOR)
        source = edge.get_source()
        dest   = edge.get_destination()
        if (not source in r) and (not dest in r):
            g.del_edge(source, dest)
        if (source in r) != (dest in r):
            raise Exception("Edge half attached to root nodes")

    for node in g.get_node_list():
        if node.get("color") is None:
            node.set("color", FOREGROUND_COLOR)
        if node.get("fontcolor") is None:
            node.set("fontcolor", FOREGROUND_COLOR)
        if not node.get_name() in r:
            g.del_node(node.get_name())

    text_file = open(filename, "wb")
    text_file.write(g.create_dot())
    text_file.close()

(world,)=pydot.graph_from_dot_file("OWER.dot")

roots = [ "Links", "ToT" ]

class TextWindow(object):
    def __init__(self, master, node, canvas):
        self.node = node
        self.canvas = canvas
        top = self.top = Toplevel(master)
        top.title("region notes")
        t = self.t = Text(top, width=40, height=12)
        t.insert('1.0', node.get("label")[1:-2])
        self.t.pack()
        self.b = Button(top, text='Ok', command=self.finish)
        self.b.pack()

    def finish(self):
        self.node.set("label", "\"" + self.t.get('1.0', 'end') + "\"")
        self.top.destroy()
        self.canvas.redraw()

def new_edge(a_region, b_region):
    edge = pydot.Edge(a_region, b_region)
    edge.set("color", FOREGROUND_COLOR)
    edge.set("fontcolor", FOREGROUND_COLOR)
    return edge

class TrackerCanvas(Canvas):

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.bind("<ButtonPress-1>", self.startDrag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.stopDrag)
        self.bind("<ButtonPress-3>", self.menu)
        self.redraw()

    def add_root(self, r):
        roots.append(r)
        self.redraw()

    def svg_get_clicked_thing(self, x, y):

        def prune_svg_junk(s):
            return s.split("}")[1]

        svg_x = float(self.et.attrib["width"].split("pt")[0]) * float(x) / float(self.width)
        svg_y = float(self.et.attrib["height"].split("pt")[0]) * (float(y) / float(self.height) - 1)
        for level1 in self.et:
            for level2 in level1:
                tag = prune_svg_junk(level2.tag)
                if tag == "g":
                    hit = False
                    title = None
                    for level3 in level2:
                        tag = prune_svg_junk(level3.tag)
                        attrib = level3.attrib
                        if      tag == "ellipse" and \
                                float(svg_x) > float(attrib["cx"]) - float(attrib["rx"]) and \
                                float(svg_x) < float(attrib["cx"]) + float(attrib["rx"]) and \
                                float(svg_y) > float(attrib["cy"]) - float(attrib["ry"]) and \
                                float(svg_y) < float(attrib["cy"]) + float(attrib["ry"]):
                            hit = True;
                        if      tag == "polygon":
                            points = [ (float(point.split(",")[0]), float(point.split(",")[1])) \
                                            for point in attrib["points"].split(" ") ]
                            (x_max, y_max) = points[0]
                            (x_min, y_min) = points[0]
                            for (x, y) in points:
                                if x > x_max:
                                    x_max = x;
                                if y > y_max:
                                    y_max = y;
                                if x < x_min:
                                    x_min = x;
                                if y < y_min:
                                    y_min = y;
                            if  float(svg_x) > x_min and float(svg_x) < x_max and \
                                float(svg_y) > y_min and float(svg_y) < y_max:
                                hit = True;
                        if      tag == "title":
                            title = level3.text
                    if hit:
                        return title
        return None

    def redraw(self):

        graph_reduce(world, roots, "reduced.dot")

        if platform.system() == "Windows":
            stem = os.path.dirname(os.path.realpath(__file__)) + "/windows/"
            dot_path = mangle_path(stem + "graphviz/dot.exe")
        else:
            dot_path = "dot"

        subprocess.call((dot_path + " -Tpng -o reduced.png reduced.dot").split(" "))
        subprocess.call((dot_path + " -Tsvg -o reduced.svg reduced.dot").split(" "))

        self.et = xml.etree.ElementTree.parse('reduced.svg').getroot()
        self.f = PhotoImage(file="reduced.png")
        self.width = self.f.width()
        self.height = self.f.height()

        self.window.geometry(str(self.width) + "x" + str(self.height))
        self.config(width=self.width, height=self.height)
        self.create_image(0, 0, anchor=NW, image=self.f)
        self.pack()
    
    def menu(self, event):
        popup = Menu(window, tearoff=0)
        for n in world.get_node_list():
            if not n.get_name() in roots and n.get("label") != "\"?\"" and \
                                             n.get("label") != "\"Owl?\"":
                def add_command(name):
                    popup.add_command(label=n.get_name(), command = lambda : self.add_root(name))
                add_command(n.get_name())
        popup.add_separator()
        popup.add_command(label="Cancel")
        try:
            popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            popup.grab_release()

    def startDrag(self, event):
        self.startx = event.x
        self.starty = event.y

    def drag(self, event):
        self.delete(self.find_withtag('line'))
        self.create_line(self.startx, self.starty, event.x, event.y, arrow=BOTH, width=3, tag='line', fill="blue")

    def stopDrag(self, event):
        self.delete(self.find_withtag('line'))
        start = self.svg_get_clicked_thing(self.startx, self.starty)
        finish = self.svg_get_clicked_thing(event.x, event.y)
        self.do_connection(start, finish)

    def do_connection_unidirectional(self, a, b):
        if a is None or b is None:
            return False
        an = world.get_node(a)[0]
        bn = world.get_node(b)[0]
        if      a == b and \
                an.get("shape") == "\"box\"":
                popup = TextWindow(window, an, self)
                self.window.wait_window(popup.top)
                return True
        if      an.get("shape") == "\"circle\"" and \
                an.get("label") == "\"?\"":
            if  a == b or \
                bn.get("shape") != "\"circle\"" or \
                bn.get("label") != "\"?\"":
                return False
            a_region = None
            b_region = None
            a_label = None
            b_label = None
            for edge in world.get_edge_list():
                if edge.get_destination() == a:
                    a_label = edge.get("label")
                    a_region = edge.get_source()
                if edge.get_destination() == b:
                    b_label = edge.get("label")
                    b_region = edge.get_source()
            connector = new_edge(a_region, b_region)
            connector.set("taillabel", a_label)
            connector.set("headlabel", b_label)
            connector.set("headlabel", b_label)
            connector.set("arrowhead", "\"none\"")
            connector.set("arrowtail", "\"none\"")
            connector.set("minlen", "2.0")
            world.add_edge(connector)
            world.del_edge(a_region, a)
            world.del_edge(b_region, b)
            self.redraw()
            return True
        elif    an.get("shape") == "\"circle\"" and \
                an.get("label") == "\"Owl?\""   and \
                bn.get("shape") == "\"box\"":
            for edge in world.get_edge_list():
                if edge.get_destination() == a:
                    a_label = edge.get("label")
                    a_region = edge.get_source()
            connector = new_edge(a_region, b)
            connector.set("label", "Owl")
            world.del_edge(a_region, a)
            world.add_edge(connector)
            self.redraw()
            return True
        elif    an.get("shape") == "\"circle\"" and \
                bn.get("shape") == "\"box\"":
            connector = new_edge(a, b)
            world.add_edge(connector)
            self.redraw()
            return True
        else:
            return False

    def do_connection(self, a, b):
        if (not self.do_connection_unidirectional(a, b)) :
            self.do_connection_unidirectional(b, a)

window = Tk()
window.title("Rattrack")

TrackerCanvas(window)

window.mainloop()