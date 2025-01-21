import networkx as nx
from pyvis.network import Network

def create_practice_system_diagram():
    # Create a directed graph
    G = nx.DiGraph()
    
    # Create pyvis network with template path
    net = Network(
        notebook=False,
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        directed=True
    )

    # Add nodes with detailed components
    G.add_node('PracticeUI', label='Practice UI\n(HTML/JS Templates)\n- Renders practice interface\n- Handles user interactions\n- Manages client-side state')
    G.add_node('PracticeRoutes', label='Practice Routes\n(Flask Blueprint)\n- Handles HTTP requests\n- Routes to appropriate services\n- Manages API endpoints')
    G.add_node('PracticeTracker', label='Practice Tracker\n(utils/practice_tracker.py)\n- Tracks user attempts\n- Validates problem answers\n- Manages practice sessions')
    G.add_node('ProgressService', label='Progress Service\n(services/progress_service.py)\n- Calculates user progress\n- Generates performance reports\n- Tracks mastery levels')
    G.add_node('Database', label='Database\n(SQLAlchemy Models)\n- Stores all application data\n- Manages data relationships\n- Handles data persistence')
    G.add_node('MathProblems', label='Math Problems\n(utils/math_problems.py)\n- Generates math problems\n- Validates problem solutions\n- Manages problem difficulty')
    G.add_node('AuthSystem', label='Auth System\n(routes/auth_routes.py)\n- Handles user authentication\n- Manages session security\n- Controls access permissions')
    G.add_node('UserModel', label='User Model\n(models/user.py)\n- Defines user attributes\n- Manages user relationships\n- Handles user data operations')
    G.add_node('Templates', label='Templates\n(templates/practice/)\n- Contains HTML templates\n- Defines UI structure\n- Handles view rendering')
    G.add_node('StaticAssets', label='Static Assets\n(static/js/practice.js)\n- Contains JavaScript/CSS\n- Manages client-side logic\n- Handles UI interactions')
    G.add_node('WebSockets', label='Real-time\n(websockets/quiz.py)\n- Handles real-time updates\n- Manages WebSocket connections\n- Pushes notifications')

    # Add function and route nodes
    G.add_node('GetPracticeProblems', label='get_practice_problems()\n(routes/practice_routes.py)\n- Fetches practice problems\n- Validates user level\n- Returns problem set')
    G.add_node('TrackAttempt', label='track_attempt()\n(utils/practice_tracker.py)\n- Records user attempt\n- Calculates accuracy\n- Updates session stats')
    G.add_node('GenerateReport', label='generate_progress_report()\n(services/progress_service.py)\n- Creates progress report\n- Calculates metrics\n- Formats output')
    G.add_node('AuthMiddleware', label='auth_middleware()\n(routes/auth_routes.py)\n- Verifies JWT tokens\n- Checks permissions\n- Manages session state')
    G.add_node('GenerateMathProblem', label='generate_math_problem()\n(utils/math_problems.py)\n- Creates math problems\n- Validates difficulty\n- Ensures variety')
    G.add_node('ValidateAnswer', label='validate_answer()\n(utils/mractice_tracker.py)\n- Checks correctness\n- Calculates response time\n- Updates problem stats')
    G.add_node('UpdateProgress', label='update_progress()\n(services/progress_service.py)\n- Tracks mastery\n- Updates skill levels\n- Stores results')

    # Add detailed edges with interaction types
    G.add_edge('PracticeRoutes', 'GetPracticeProblems', label='Invoke\nProblem Request')
    G.add_edge('GetPracticeProblems', 'PracticeTracker', label='Validate\nUser Level')
    G.add_edge('GetPracticeProblems', 'MathProblems', label='Generate\nProblem Set')
    G.add_edge('PracticeRoutes', 'TrackAttempt', label='Submit\nAttempt Data')
    G.add_edge('TrackAttempt', 'ProgressService', label='Update\nUser Stats')
    G.add_edge('PracticeRoutes', 'GenerateReport', label='Request\nProgress Report')
    G.add_edge('AuthMiddleware', 'PracticeRoutes', label='Verify\nAuthentication')
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

    # Add nodes to pyvis network with colors and labels
    node_colors = {
        'UI Layer': '#a6cee3',
        'Application Layer': '#b2df8a',
        'Service Layer': '#fdbf6f',
        'Data Layer': '#fb9a99'
    }
    
    # Add nodes with their respective colors
    for node in G.nodes():
        layer = 'UI Layer' if node in ['PracticeUI', 'Templates', 'StaticAssets'] else \
                'Application Layer' if node in ['PracticeRoutes', 'AuthSystem', 'WebSockets'] else \
                'Service Layer' if node in ['PracticeTracker', 'ProgressService', 'MathProblems'] else \
                'Data Layer'
        
        net.add_node(node, 
                    label=G.nodes[node]['label'],
                    color=node_colors[layer],
                    shape='box',
                    font={'size': 12},
                    margin=10,
                    widthConstraint=300)

    # Add edges with labels
    for edge in G.edges(data=True):
        net.add_edge(edge[0], edge[1], label=edge[2]['label'], arrows='to')

    # Configure physics for better layout
    net.set_options("""
    {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.3,
          "springLength": 200,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 0.1
        },
        "minVelocity": 0.75,
        "solver": "barnesHut"
      }
    }
    """)

    # Save and show the interactive network
    net.show('practice_system.html')

if __name__ == '__main__':
    create_practice_system_diagram()
