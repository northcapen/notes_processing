import json
import os

import networkx as nx
import pandas as pd
from prefect import flow, task

from evernote2md.tasks.source import read_notes_dataframe, read_links_dataframe

@task
def build_cosma(context_dir):
    notes = read_notes_dataframe(context_dir)
    links = read_links_dataframe(context_dir)
    links.index.name = 'id'
    links = links.rename(columns={'from_guid' : 'source', 'to_guid' : 'target'}).reset_index()
    target = context_dir + '/cosma/'
    os.makedirs(target, exist_ok=True)
    notes.to_csv(target + 'notes.csv', index=False)
    links.to_csv(target + 'links.csv', index=False)


@task
def build_graph_ml(context_dir, notes, links):
    vertices = list(notes['id'])
    edges = links[['from_guid', 'to_guid']]
    edges = [(e[1], e[2]) for e in edges.itertuples()]

    G = nx.MultiDiGraph()
    G.add_nodes_from(vertices)
    G.add_edges_from(edges)

    connected_components = sorted(nx.connected_components(G.to_undirected()), key=len, reverse=True)
    largest_component = connected_components[0]

    G_main = G.subgraph(largest_component).copy()
    nx.write_graphml(G, f'{context_dir}/notes.graphml')
    nx.write_graphml(G_main, f'{context_dir}/notes_main.graphml')
    # nx.write_gexf(G, 'notes.gexf')
    return G_main

@task
def build_d3_json(context_dir, notes, links, G_main):
    output_json = context_dir + '/d3.json'

    print(G_main.nodes)

    nodes_list = [{
        "id": row["title"],
        "group": 1
    } for index, row in notes.iterrows() if row["id"] in G_main.nodes]
    links = links.query('~to_guid.isnull()')


    # Process links DataFrame
    links_list = [{
        "source": row["from_title"],
        "target": row["to_new"] if pd.notna(row["to_new"]) else row["to_old"],
        "value": 1  # Assuming a default value of 1 for all links; adjust as necessary
    } for index, row in links.iterrows() if row["from_guid"] in G_main.nodes and row[
        "to_guid"] in G_main.nodes]

    # Combine into a single dictionary
    output_dict = {
        "nodes": nodes_list,
        "links": links_list
    }

    # Write to JSON file
    with open(output_json, 'w', encoding='utf-8') as json_file:
        json.dump(output_dict, json_file, indent=4, ensure_ascii=False)

    print(f"Data successfully written to {output_json}")


@flow
def build_graph_stuff(context_dir):
    notes = read_notes_dataframe(context_dir)
    links = read_links_dataframe(context_dir)

    G_main = build_graph_ml(context_dir, notes, links)
    build_d3_json(context_dir, notes, links, G_main)
    #build_cosma()