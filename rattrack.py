#!/usr/bin/python3

from tkinter import *
import subprocess
import xml.etree.ElementTree
import os
import platform

FOREGROUND_COLOR="#787878"

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

def unparse_interiors(interiors):
    ret = interiors["title"]
    if (interiors["woth"].get()):
        ret += " (Hero)"
    if (interiors["fool"].get()):
        ret += " (Fool)"
    ret += "\n"
    for segment in interiors["segments"]:
        ret += "\n"
        for interior in segment:
            if interior["checked"].get():
                continue
            ret += interior["name"]
            if interior["notes"].get():
                ret += " : " + interior["notes"].get()
            else:
                ret += " ?"
            ret += "\n"
    return ret

def parse_interiors(text):
    ret = None;
    segment = None;
    for line in [ line_unstripped.strip("\"") for line_unstripped in text.splitlines()]:
        if ret is None:
            woth = IntVar()
            woth.set(0)
            fool = IntVar()
            fool.set(0)
            ret = { "title" : line, "segments" : [], "woth" : woth, "fool" : fool }
            continue
        if line:
            checked = IntVar()
            checked.set(0)
            notes = StringVar()
            notes.set("")
            segment.append({ "checked" : checked, "name" : line, "notes" : notes })
        else:
            if segment is not None:
                ret["segments"].append(segment)
            segment = []
    if segment and len(segment) != 0:
        ret["segments"].append(segment)
    return ret

window = Tk()
window.title("Rattrack")

roots = [ "Links", "ToT" ]
edges = {}
interiorss = {}

for node in world.get_node_list():
    edges[node.get_name()] = []
    if node.get("shape") == "\"box\"":
        interiors = parse_interiors(node.get("label"))
        node.set("label", unparse_interiors(interiors))
        interiorss[node.get_name()] = interiors

class TextWindow(object):
    def __init__(self, master, node, canvas):
        self.node = node
        self.canvas = canvas
        top = self.top = Toplevel(master)
        top.protocol("WM_DELETE_WINDOW", self.finish)

        self.interiors = interiors = interiorss[node.get_name()]
        top.title(interiors["title"])

        checkedlabel = Label(top, text = "Cleared")
        interiorlabel = Label(top, text = "Interior")
        noteslabel = Label(top, text = "Notes")
        checkedlabel.grid(row=0, column=1, padx=15, pady=15)
        interiorlabel.grid(row=0, column=0, padx=15, pady=15, sticky=W)
        noteslabel.grid(row=0, column=2, padx=15, pady=15)

        row = 1
        for segment in interiors["segments"]:
            for interior in segment:
                checkbutton = Checkbutton(top, variable = interior["checked"])
                label = Label(top, text = interior["name"])
                notes = Entry(top, textvariable = interior["notes"])
                checkbutton.grid(row=row, column=1, padx=15)
                label.grid(row=row, column=0, padx=15, sticky=W)
                notes.grid(row=row, column=2, padx=15)
                row += 1
            top.grid_rowconfigure(row, minsize=20)
            row += 1

        #OOTR specific
        woth = Checkbutton(top, text="Way of the Hero", variable = interiors["woth"])
        fool = Checkbutton(top, text="A Foolish Choice", variable = interiors["fool"])
        woth.grid(row=row, column=0, columnspan=3, sticky=W)
        row += 1
        fool.grid(row=row, column=0, columnspan=3, sticky=W)
        row += 1
        top.grid_rowconfigure(row, minsize=20)
        row += 1

        ok = Button(top, text='Ok', command=self.finish)
        ok.grid(row=row, column=0, columnspan=3)

    def finish(self):
        self.node.set("label", unparse_interiors(self.interiors))
        self.top.destroy()
        self.canvas.redraw()

def new_edge(a_region, b_region, replaces, headlabel=None, taillabel=None):
    edge = pydot.Edge(a_region, b_region)
    edge.set("color", FOREGROUND_COLOR)
    edge.set("fontcolor", FOREGROUND_COLOR)
    edge_data = { "active" : True, "edge":edge, "replaces" : replaces }
    edges[a_region].append(edge_data)
    edges[b_region].append(edge_data)
    name = a_region
    if taillabel is not None:
        name += ":" + taillabel
        edge.set("taillabel", taillabel)
    name += " <-> " + b_region
    if headlabel is not None:
        name += ":" + headlabel
        edge.set("headlabel", headlabel)
    edge.set("name", name)
    world.add_edge(edge)
    for replace in replaces:
        world.del_edge(replace)
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

    def del_root(self, r):
        roots.remove(r)
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

    def del_edge(self, edge_data):
        #Just leak it
        edge_data["active"] = False;
        world.del_edge(edge_data["edge"])
        for replace in edge_data["replaces"]:
            world.add_edge(replace)
        self.redraw()

    def name_del(self, label, clicked):
        for piece in label.split(" <-> "):
            try:
                subpieces = piece.split(":")
                if subpieces[0] == clicked:
                    return "disconnect " + subpieces[1] + " exit"
            except:
                pass
        if label.split(" <-> ")[1] == clicked:
            return "disconnect " + label.split(" <-> ")[0]
        return None

    def menu(self, event):
        popup = Menu(window, tearoff=0)
        space = True

        clicked = self.svg_get_clicked_thing(event.x, event.y)
        if clicked is not None:
            clickedn = world.get_node(clicked)[0]
            if clickedn.get("shape") == "\"box\"":
                space = False
                connected_to_something = False
                for edge_data in edges[clicked]:
                    if edge_data["active"]:
                        d = self.name_del(edge_data["edge"].get("name"), clicked)
                        def add_del_command(edge_data):
                            popup.add_command(label=d, command = lambda : self.del_edge(edge_data))
                        if d is not None:
                            add_del_command(edge_data)
                            connected_to_something = True
                if not connected_to_something:
                    if not clicked in roots:
                        return
                    def add_remove_command(name):
                        popup.add_command(label="remove", command = lambda : self.del_root(name))
                    add_remove_command(clicked)

        if space:
            for n in world.get_node_list():
                if not n.get_name() in roots and n.get("label") != "\"?\"" and \
                                                 n.get("label") != "\"Owl?\"":
                    def add_command(name):
                        popup.add_command(label=interiorss[n.get_name()]["title"], \
                                          command = lambda : self.add_root(name))
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
            replaces = []
            for edge in world.get_edge_list():
                if edge.get_destination() == a:
                    a_label = edge.get("label")
                    a_region = edge.get_source()
                    replaces.append(edge)
                if edge.get_destination() == b:
                    b_label = edge.get("label")
                    b_region = edge.get_source()
                    replaces.append(edge)
            connector = new_edge(a_region, b_region, replaces, taillabel=a_label, headlabel=b_label)
            connector.set("arrowhead", "\"none\"")
            connector.set("arrowtail", "\"none\"")
            connector.set("minlen", "2.0")
            self.redraw()
            return True
        elif    an.get("shape") == "\"circle\"" and \
                an.get("label") == "\"Owl?\""   and \
                bn.get("shape") == "\"box\"":
            for edge in world.get_edge_list():
                if edge.get_destination() == a:
                    a_label = edge.get("label")
                    a_region = edge.get_source()
                    a_edge = edge
            connector = new_edge(a_region, b, [a_edge], taillabel="Owl")
            self.redraw()
            return True
        elif    an.get("shape") == "\"circle\"" and \
                bn.get("shape") == "\"box\"":
            connector = new_edge(a, b, [])
            self.redraw()
            return True
        else:
            return False

    def do_connection(self, a, b):
        if (not self.do_connection_unidirectional(a, b)) :
            self.do_connection_unidirectional(b, a)

TrackerCanvas(window)

window.mainloop()
