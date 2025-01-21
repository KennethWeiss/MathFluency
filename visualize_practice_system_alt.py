import networkx as nx
import matplotlib.pyplot as plt

def create_practice_system_diagram():
    G = nx.DiGraph()

    # Add nodes with detailed components
    G.add_node('PracticeUI', label='Practice UI\n(HTML/JS Templates)')
    G.add_node('PracticeRoutes', label='Practice Routes\n(Flask Blueprint)')
    G.add_node('PracticeTracker', label='Practice Tracker\n(utils/practice_tracker.py)')
    G.add_node('ProgressService', label='Progress Service\n(services/progress_service.py)')
    G.add_node('Database', label='Database\n(SQLAlchemy Models)')
    G.add_node('MathProblems', label='Math Problems\n(utils/math_problems.py)')
    G.add_node('AuthSystem', label='Auth System\n(routes/auth_routes.py)')
    G.add_node('UserModel', label='User Model\n(models/user.py)')
    G.add_node('Templates', label='Templates\n(templates/practice/)')
    G.add_node('StaticAssets', label='Static Assets\n(static/js/practice.js)')
    G.add_node('WebSockets', label='Real-time\n(websockets/quiz.py)')
    
    # Add detailed edges with interaction types
    G.add_edge('PracticeUI', 'PracticeRoutes', label='AJAX/HTTP\nRequests')
    G.add_edge('PracticeRoutes', 'PracticeTracker', label='Get Problems\nValidate Input')
    G.add_edge('PracticeRoutes', 'ProgressService', label='Check Progress\nUpdate Stats')
    G.add_edge('PracticeTracker', 'Database', label='Store Attempts\nLog Results')
    G.add_edge('ProgressService', 'Database', label='Query Stats\nGenerate Reports')
    G.add_edge('MathProblems', 'PracticeTracker', label='Generate Problems\nValidate Answers')
    G.add_edge('AuthSystem', 'PracticeRoutes', label='Authentication\nAuthorization')
    G.add_edge('UserModel', 'Database', label='ORM Mapping\nUser Data')
    G.add_edge('Templates', 'PracticeUI', label='Render Views\nHandle Events')
    G.add_edge('StaticAssets', 'PracticeUI', label='Client Logic\nUI Interactions')
    G.add_edge('WebSockets', 'PracticeUI', label='Real-time Updates\nNotifications')

    # Draw graph with improved layout
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    # Draw nodes with different colors for layers
    node_colors = {
        'UI Layer': 'lightblue',
        'Application Layer': 'lightgreen',
        'Service Layer': 'orange',
        'Data Layer': 'pink'
    }
    
    nx.draw_networkx_nodes(G, pos, nodelist=['PracticeUI', 'Templates', 'StaticAssets'], 
                         node_size=4000, node_color=node_colors['UI Layer'])
    nx.draw_networkx_nodes(G, pos, nodelist=['PracticeRoutes', 'AuthSystem', 'WebSockets'], 
                         node_size=4000, node_color=node_colors['Application Layer'])
    nx.draw_networkx_nodes(G, pos, nodelist=['PracticeTracker', 'ProgressService', 'MathProblems'], 
                         node_size=4000, node_color=node_colors['Service Layer'])
    nx.draw_networkx_nodes(G, pos, nodelist=['Database', 'UserModel'], 
                         node_size=4000, node_color=node_colors['Data Layer'])
    
    # Draw edges with different styles
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20, 
                          edge_color='gray', width=2)
    
    # Draw labels with improved formatting
    node_labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels=node_labels, 
                           font_size=9, font_weight='bold')
    
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                font_size=8, label_pos=0.4)
    
    # Add legend
    for layer, color in node_colors.items():
        plt.scatter([], [], c=color, label=layer)
    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, 
              title='System Layers', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.title('Detailed Practice System Architecture', pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    create_practice_system_diagram()
