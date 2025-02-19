// Quiz Game Logic
class QuizGame {
    constructor(quizId, isTeacher = false) {
        this.quizId = quizId;
        this.isTeacher = isTeacher;
        this.score = 0;
        this.streak = 0;
        this.timer = null;
        this.timeLeft = 0;
        this.currentProblem = null;
        this.currentAnswer = null;

        // Setup socket
        this.socket = io({
            transports: ['websocket'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });

        // Cache elements that exist in this view
        this.elements = this.cacheElements();
        
        // Setup socket listeners
        this.setupSocketListeners();
    }

    cacheElements() {
        const elements = {};
        
        // Elements for both views
        elements.status = document.getElementById('quiz-status');
        
        // Elements only for student view
        if (!this.isTeacher) {
            elements.problem = document.getElementById('problem-display');
            elements.answer = document.getElementById('answer');
            elements.score = document.getElementById('current-score');
            elements.feedback = document.getElementById('feedback');
        }
        
        return elements;
    }

    displayProblem(problem) {
        if (this.isTeacher) return;
        
        console.log('Displaying problem:', problem);
        this.currentProblem = problem;
        if (this.elements.problem) {
            this.elements.problem.textContent = problem.text || problem;
            if (this.elements.answer) {
                this.elements.answer.value = '';
                this.elements.answer.focus();
            }
        }
    }

    startQuiz() {
        console.log('Starting quiz...');
        this.socket.emit('start_quiz', { quiz_id: this.quizId });
    }

    pauseQuiz() {
        console.log('Pausing quiz...');
        this.socket.emit('pause_quiz', { quiz_id: this.quizId });
    }

    resumeQuiz() {
        console.log('Resuming quiz...');
        this.socket.emit('resume_quiz', { quiz_id: this.quizId });
    }

    endQuiz() {
        console.log('Ending quiz...');
        this.socket.emit('end_quiz', { quiz_id: this.quizId });
    }

    submitAnswer(answer) {
        console.log('Submitting answer:', answer);
        this.socket.emit('submit_answer', {
            quiz_id: this.quizId,
            answer: answer,
            time_taken: this.timeLeft
        });
    }

    showFeedback(correct) {
        if (!this.elements.feedback) return;
        
        this.elements.feedback.textContent = correct ? '✓ Correct!' : '✗ Wrong!';
        this.elements.feedback.className = `alert ${correct ? 'alert-success' : 'alert-danger'} mb-3`;
        this.elements.feedback.classList.remove('d-none');
        
        setTimeout(() => {
            this.elements.feedback.classList.add('d-none');
        }, 2000);
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.socket.emit('join_quiz', {
                quiz_id: this.quizId,
                is_teacher: this.isTeacher
            });
        });

        // Handle quiz status changes
        this.socket.on('quiz_status_changed', (data) => {
            console.log('Quiz status changed:', data);
            if (data.quiz_id == this.quizId) {
                this.updateScreens(data.status);
            }
        });

        // Handle new problems
        this.socket.on('new_problem', (data) => {
            console.log('New problem received:', data);
            if (data.quiz_id == this.quizId) {
                this.currentAnswer = data.answer;
                this.displayProblem(data.problem);
            }
        });

        // Handle answer feedback
        this.socket.on('answer_feedback', (data) => {
            if (data.quiz_id == this.quizId) {
                this.showFeedback(data.correct);
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
        });
    }

updateScreens(status) {
    // Get all screen elements
    const screens = {
        waiting: document.getElementById('waiting-screen'),
        quiz: document.getElementById('quiz-screen'),
        paused: document.getElementById('paused-screen'),
        finished: document.getElementById('finished-screen')
    };
    
    // Hide all screens
    Object.values(screens).forEach(screen => {
        if (screen) screen.classList.add('d-none');
    });
    
    // Show the appropriate screen
    const screenMap = {
        'waiting': screens.waiting,
        'active': screens.quiz,
        'paused': screens.paused,
        'finished': screens.finished
    };
    
    const targetScreen = screenMap[status];
    if (targetScreen) {
        console.log(`Showing ${status} screen`);
        targetScreen.classList.remove('d-none');
    }

    // Update button visibility based on status
    const startButton = document.getElementById('start-quiz-btn');
    const pauseButton = document.getElementById('pause-quiz-btn');
    const resumeButton = document.getElementById('resume-quiz-btn');
    const endButton = document.getElementById('end-quiz-btn');

    if (status === 'waiting') {
        if (startButton) startButton.style.display = 'block';
        if (pauseButton) pauseButton.style.display = 'none';
        if (resumeButton) resumeButton.style.display = 'none';
        if (endButton) endButton.style.display = 'none';
} else if (status === 'active') {
    if (startButton) startButton.style.display = 'none';
    if (pauseButton) pauseButton.style.display = 'block';
    if (resumeButton) resumeButton.style.display = 'none';
    if (endButton) endButton.style.display = 'block';
} else if (status === 'paused') {
    if (startButton) startButton.style.display = 'none';
    if (pauseButton) pauseButton.style.display = 'none';
    if (resumeButton) resumeButton.style.display = 'block';
    if (endButton) endButton.style.display = 'block';
    } else if (status === 'finished') {
        if (startButton) startButton.style.display = 'none';
        if (pauseButton) pauseButton.style.display = 'none';
        if (resumeButton) resumeButton.style.display = 'none';
        if (endButton) endButton.style.display = 'none';
    }
}
}
