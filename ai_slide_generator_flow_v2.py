#!/usr/bin/env python3
"""
AI Slide Generator Workflow Visualization

This script generates an interactive D3.js visualization of the AI Slide Generator workflow.
It shows the relationships between different agents and the flow of data between them.
"""

import os
import webbrowser
from pathlib import Path

# Define the HTML template for the D3.js visualization
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Slide Generator Workflow</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        
        #workflow-container {
            width: 100%;
            height: 800px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .node {
            cursor: pointer;
        }
        
        .node rect {
            stroke-width: 2px;
        }
        
        .node-text {
            font-size: 12px;
            font-weight: bold;
            text-anchor: middle;
            dominant-baseline: middle;
            pointer-events: none;
        }
        
        .node-desc {
            font-size: 10px;
            text-anchor: middle;
            dominant-baseline: middle;
            pointer-events: none;
        }
        
        .link {
            fill: none;
            stroke-width: 2px;
        }
        
        .link-label {
            font-size: 10px;
            pointer-events: none;
            text-anchor: middle;
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            max-width: 300px;
        }
        
        .legend {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        
        .legend-color {
            width: 15px;
            height: 15px;
            margin-right: 10px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <h1>AI Slide Generator Agent Workflow</h1>
    
    <div id="workflow-container"></div>
    
    <script>
        // Define the workflow data
        const data = {
            nodes: [
                { id: "user", name: "User", desc: "Requests slide generation", type: "user", group: "input" },
                { id: "orchestrator", name: "Orchestrator", desc: "Coordinates overall workflow", type: "agent", group: "core" },
                { id: "monitoring", name: "Monitoring", desc: "Evaluates intermediate steps", type: "agent", group: "support" },
                { id: "research", name: "Research", desc: "Collects information", type: "agent", group: "primary" },
                { id: "outline", name: "Outline", desc: "Creates slide structure", type: "agent", group: "primary" },
                { id: "template", name: "Template Selector", desc: "Chooses appropriate theme", type: "agent", group: "primary" },
                { id: "slide_writer", name: "Slide Writer", desc: "Creates slide content", type: "agent", group: "primary" },
                { id: "image_fetch", name: "Image Fetch", desc: "Finds relevant images", type: "agent", group: "support" },
                { id: "refiner", name: "Refiner", desc: "Improves and polishes slides", type: "agent", group: "primary" },
                { id: "html_output", name: "HTML Presentation", desc: "Final output", type: "output", group: "output" }
            ],
            links: [
                { source: "user", target: "orchestrator", label: "Topic & Parameters" },
                { source: "orchestrator", target: "research", label: "Search Query" },
                { source: "research", target: "orchestrator", label: "Research Results" },
                { source: "orchestrator", target: "outline", label: "Research Data" },
                { source: "outline", target: "orchestrator", label: "Slide Outline" },
                { source: "orchestrator", target: "template", label: "Topic & Style" },
                { source: "template", target: "orchestrator", label: "Theme" },
                { source: "orchestrator", target: "slide_writer", label: "Outline & Theme" },
                { source: "slide_writer", target: "image_fetch", label: "Image Requests" },
                { source: "image_fetch", target: "slide_writer", label: "Image URLs" },
                { source: "slide_writer", target: "orchestrator", label: "Draft Slides" },
                { source: "orchestrator", target: "refiner", label: "Draft Presentation" },
                { source: "refiner", target: "orchestrator", label: "Refined Slides" },
                { source: "orchestrator", target: "html_output", label: "Final Presentation" },
                { source: "monitoring", target: "research", label: "Quality Check", dashed: true },
                { source: "monitoring", target: "outline", label: "Quality Check", dashed: true },
                { source: "monitoring", target: "slide_writer", label: "Quality Check", dashed: true },
                { source: "monitoring", target: "refiner", label: "Quality Check", dashed: true },
                { source: "orchestrator", target: "monitoring", label: "Monitoring Requests", dashed: true }
            ]
        };

        // Define group colors
        const groupColors = {
            "input": "#B3E5FC",
            "core": "#FFD54F",
            "primary": "#C8E6C9",
            "support": "#E1BEE7",
            "output": "#FFCCBC"
        };

        // Create the D3 force directed graph
        const width = document.getElementById("workflow-container").offsetWidth;
        const height = document.getElementById("workflow-container").offsetHeight;
        
        const svg = d3.select("#workflow-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        // Add arrow marker definitions
        svg.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("orient", "auto")
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");
            
        // Add dashed arrow marker definition
        svg.append("defs").append("marker")
            .attr("id", "arrowhead-dashed")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("orient", "auto")
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");

        // Create tooltip
        const tooltip = d3.select("body")
            .append("div")
            .attr("class", "tooltip");

        // Create the force simulation
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("x", d3.forceX(width / 2).strength(0.1))
            .force("y", d3.forceY(height / 2).strength(0.1));

        // Draw the links
        const link = svg.append("g")
            .selectAll("path")
            .data(data.links)
            .enter().append("path")
            .attr("class", "link")
            .attr("stroke", "#999")
            .attr("stroke-dasharray", d => d.dashed ? "5,5" : "0")
            .attr("marker-end", d => d.dashed ? "url(#arrowhead-dashed)" : "url(#arrowhead)");

        // Draw link labels
        const linkLabel = svg.append("g")
            .selectAll("text")
            .data(data.links)
            .enter().append("text")
            .attr("class", "link-label")
            .attr("dy", -5)
            .text(d => d.label)
            .attr("fill", "#666");

        // Draw the nodes
        const node = svg.append("g")
            .selectAll(".node")
            .data(data.nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Add rectangles for nodes
        node.append("rect")
            .attr("width", d => Math.max(d.name.length * 8, 80))
            .attr("height", 40)
            .attr("rx", 5)
            .attr("ry", 5)
            .attr("x", d => -Math.max(d.name.length * 8, 80) / 2)
            .attr("y", -20)
            .attr("fill", d => groupColors[d.group])
            .attr("stroke", d => d3.rgb(groupColors[d.group]).darker(0.5));

        // Add text labels
        node.append("text")
            .attr("class", "node-text")
            .text(d => d.name);
            
        // Add text descriptions
        node.append("text")
            .attr("class", "node-desc")
            .attr("dy", 15)
            .text(d => d.desc);

        // Add node interactions
        node.on("mouseover", function(event, d) {
            // Show tooltip
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
                
            let tooltipText = `<strong>${d.name}</strong><br>${d.desc}<br><br>`;
            tooltipText += d.type === "agent" ? "Type: Agent<br>" : `Type: ${d.type}<br>`;
            
            // Find connections
            const connections = data.links.filter(link => link.source.id === d.id || link.target.id === d.id);
            
            if (connections.length > 0) {
                tooltipText += "<br><strong>Connections:</strong><br>";
                connections.forEach(conn => {
                    if (conn.source.id === d.id) {
                        tooltipText += `→ Sends ${conn.label} to ${conn.target.name}<br>`;
                    } else {
                        tooltipText += `← Receives ${conn.label} from ${conn.source.name}<br>`;
                    }
                });
            }
                
            tooltip.html(tooltipText)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
            
            // Highlight connections
            link.style("stroke", l => (l.source.id === d.id || l.target.id === d.id) ? "#ff7700" : "#999")
                .style("stroke-width", l => (l.source.id === d.id || l.target.id === d.id) ? 3 : 2);
        })
        .on("mouseout", function() {
            // Hide tooltip
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
                
            // Reset connection highlighting
            link.style("stroke", "#999")
                .style("stroke-width", 2);
        });
        
        // Add legend
        const legend = svg.append("g")
            .attr("class", "legend")
            .attr("transform", "translate(20, 20)");
            
        legend.append("rect")
            .attr("width", 160)
            .attr("height", 145)
            .attr("fill", "white")
            .attr("rx", 5)
            .attr("ry", 5)
            .attr("stroke", "#ddd");
            
        legend.append("text")
            .attr("x", 80)
            .attr("y", 20)
            .attr("text-anchor", "middle")
            .attr("font-weight", "bold")
            .text("Legend");
            
        const legendItems = [
            { label: "User Input", color: groupColors.input },
            { label: "Core Agent", color: groupColors.core },
            { label: "Primary Agent", color: groupColors.primary },
            { label: "Support Agent", color: groupColors.support },
            { label: "Output", color: groupColors.output }
        ];
        
        legendItems.forEach((item, i) => {
            const g = legend.append("g")
                .attr("transform", `translate(10, ${i * 25 + 35})`);
                
            g.append("rect")
                .attr("width", 15)
                .attr("height", 15)
                .attr("fill", item.color)
                .attr("stroke", d3.rgb(item.color).darker(0.5))
                .attr("rx", 3)
                .attr("ry", 3);
                
            g.append("text")
                .attr("x", 25)
                .attr("y", 12)
                .text(item.label)
                .attr("font-size", 12);
        });

        // Update positions on each simulation tick
        simulation.on("tick", () => {
            link.attr("d", d => {
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const dr = Math.sqrt(dx * dx + dy * dy);
                
                return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
            });

            linkLabel
                .attr("x", d => (d.source.x + d.target.x) / 2)
                .attr("y", d => (d.source.y + d.target.y) / 2);

            node.attr("transform", d => `translate(${d.x}, ${d.y})`);
        });

        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
        
        // Zoom functionality
        const zoom = d3.zoom()
            .scaleExtent([0.5, 3])
            .on("zoom", (event) => {
                svg.selectAll("g").attr("transform", event.transform);
            });
            
        svg.call(zoom);
    </script>
</body>
</html>
"""

def generate_workflow_visualization():
    """Generate the D3.js visualization and open it in a browser."""
    # Create the HTML file
    output_file = Path("static/output/ai_slide_generator_flow.html")
    
    # Make sure the directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the HTML content
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE)
    
    print(f"✅ Workflow visualization generated: {output_file}")
    
    # Get the absolute file path
    abs_path = output_file.absolute().as_uri()
    
    # Open in browser
    print(f"🌐 Opening in browser: {abs_path}")
    webbrowser.open(abs_path)
    
    return abs_path

if __name__ == "__main__":
    generate_workflow_visualization() 