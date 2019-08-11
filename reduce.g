BEGIN{
	void reduce_out(graph_t _g, node_t _n, edge_t _e, int _d){
		_e = fstout(_n);
		while (_e != NULL) {
			clone(_g, _e);
			if (_d < 25) {
			  reduce_out(_g, _e.head, NULL, _d + 1);
			}
			_e = nxtout(_e);
		}
	}
}

BEG_G {
	graph_t g = graph("G", "S");
	g.rankdir = "LR";
}


N [name=="ToT"] {
	node_t t = clone(g, $);
	reduce_out(g, $, NULL, 1);
}

N [name=="LinksHouse"] {
	node_t l = clone(g, $);
	reduce_out(g, $, NULL, 1);
}

END_G {
	$O = g;
}
