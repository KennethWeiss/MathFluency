// Quiz Game Logic
class QuizGame {
    constructor(quizId, isTeacher = false) {
        this.quizId = quizId;
        this.isTeacher = isTeacher;
        this.socket = io({
    transports: ['websocket'], // Use WebSocket transport
    reconnectionAttempts: 5, // Retry connection attempts
    reconnectionDelay: 1000 // Delay between reconnection attempts
        });
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
        });
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
        });
        this.score = 0;
        this.streak = 0;
        this.timer = null;
        this.timeLeft = 0;
        this.currentProblem = null;
        this.elements = this.cacheElements();
        document.addEventListener('DOMContentLoaded', () => {
            this.setupSocketListeners();
        });
    }

    cacheElements() {
        return {
            problem: document.getElementById('problem-display'),
            answer: document.getElementById('answer'),
            timer: document.getElementById('timer'),
            score: document.getElementById('score'),
            streak: document.getElementById('streak'),
            feedback: document.getElementById('feedback'),
            status: document.getElementById('quiz-status'),
            leaderboard: document.getElementById('leaderboard'),
            container: document.getElementById('quiz-container')
        };
    }

    setupSocketListeners() {
        const socketEvents = {
            'join_quiz': () => {
                console.log('Attempting to join quiz...');
                this.socket.emit('join_quiz', { 
                    quiz_id: this.quizId,
                    is_teacher: this.isTeacher 
                });
            },
            'new_problem': (data) => {
                console.log('New problem received:', data);
                this.displayProblem(data.problem);
                this.startTimer(data.timeLimit);
            },
            'answer_feedback': (data) => {
                console.log('Answer feedback received:', data);
                this.showFeedback(data.correct);
            },
            'answer_result': (data) => {
                console.log('Answer result received');
                this.handleAnswerResult(data);
            },
            'quiz_status_changed': (data) => {
                console.log('Quiz status changed:', data);
                console.log('Current quiz ID:', this.quizId);
                console.log('Data quiz ID:', data.quiz_id);
                
                // Convert quizId to a number for comparison
                if (data.quiz_id == (this.quizId)) {
                    console.log('Updating screen to:', data.status);
                    
                    // Get screen elements
                    const waitingScreen = document.getElementById('waiting-screen');
                    const quizScreen = document.getElementById('quiz-screen');
                    const pausedScreen = document.getElementById('paused-screen');
                    const finishedScreen = document.getElementById('finished-screen');
                    
                    console.log('Waiting Screen:', waitingScreen);
                    console.log('Quiz Screen:', quizScreen);
                    console.log('Paused Screen:', pausedScreen);
                    console.log('Finished Screen:', finishedScreen);
                    
                    // Hide all screens first
                    console.log('Hiding all screens');
                    if (waitingScreen) waitingScreen.classList.add('d-none');
                    if (quizScreen) quizScreen.classList.add('d-none');
                    if (pausedScreen) pausedScreen.classList.add('d-none');
                    if (finishedScreen) finishedScreen.classList.add('d-none');
                    
                    // Show appropriate screen
                    console.log('Showing screen:', data.status);
                    if (data.status == 'waiting') {
                        waitingScreen.classList.remove('d-none');
                    } else if (data.status === 'active') {
                        quizScreen.classList.remove('d-none');
                    } else if (data.status === 'paused') {
                        pausedScreen.classList.remove('d-none');
                    } else if (data.status === 'finished') {
                        finishedScreen.classList.remove('d-none');
                    }
                } else {
                    console.log('Quiz status change event for different quiz:', data.quiz_id);
                }
                console.log('Quiz status change complete');
            },
            'leaderboard_update': (data) => {
                console.log('Leaderboard update received');
                this.updateLeaderboard(data.leaderboard); // Ensure data is an array
            },
            'connect_error': (error) => {
                console.error('Socket connection error:', error);
                this.showError('Connection error. Please refresh the page.');
            }
        };

        // Set up all socket event listeners
        Object.entries(socketEvents).forEach(([event, handler]) => {
            this.socket.on(event, handler);
        });

        // Join the quiz room when socket connects
        if (this.socket.connected) {
            socketEvents['join_quiz']();
        } else {
            this.socket.once('connect', socketEvents['join_quiz']);
        }
    }

    submitAnswer(answer) {
        console.log('Submitting answer:', answer);
        if (this.timer) {
            clearInterval(this.timer);
        }
        this.socket.emit('submit_answer', {
            quiz_id: this.quizId,
            answer: answer,
            time_taken: this.getTimeTaken(),
            question_id: this.currentProblem?.id
        });
    }

    displayProblem(problem) {
        console.log('Displaying problem:', problem);
        this.currentProblem = problem;
        this.elements.problem.textContent = problem.text || problem;
        this.elements.answer.value = '';
        this.elements.answer.focus();
    }

    startTimer(duration) {
        // Convert duration to number and default to 30 seconds if invalid
        this.timeLeft = parseInt(duration) || 30;
        if (this.timer) clearInterval(this.timer);

        // Update timer display immediately
        this.elements.timer.textContent = this.timeLeft;

        this.timer = setInterval(() => {
            this.timeLeft--;
            this.elements.timer.textContent = this.timeLeft;
            
            if (this.timeLeft <= 0) {
                clearInterval(this.timer);
                this.submitAnswer(null);
            }
        }, 1000);
    }

    handleAnswerResult(data) {
        const { correct, points, streak } = data;
        this.score += points;
        this.streak = streak;

        this.elements.score.textContent = this.score;
        this.elements.streak.textContent = this.streak;
        this.showFeedback(correct);
    }

    showFeedback(correct) {
        const feedback = this.elements.feedback;
        feedback.textContent = correct ? '✓ Correct!' : '✗ Wrong!';
        feedback.className = `feedback ${correct ? 'correct' : 'wrong'}`;
        
        // Reset and trigger animation
        feedback.style.animation = 'none';
        feedback.offsetHeight;
        feedback.style.animation = 'feedbackPop 0.5s';
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'quiz-error';
        errorDiv.textContent = message;
        this.elements.container.prepend(errorDiv);
        
        setTimeout(() => errorDiv.remove(), 5000);
    }

    updateQuizStatus(data) {
        const statusElement = this.elements.status;
        console.log('updateQuizStatus called with data:', data);
        console.log('Current status:', data.status);
        console.log("Status Element: ", statusElement);
        
        // Update status text and badge color
        statusElement.textContent = data.status;
        statusElement.className = `badge bg-${
            data.status === 'active' ? 'success' : 
            data.status === 'paused' ? 'secondary' : 
            data.status === 'waiting' ? 'warning' : 
            'secondary'
        }`;

        // Get or create the button container
        let buttonContainer = document.querySelector('.quiz-control-buttons');
        if (!buttonContainer) {
            buttonContainer = document.createElement('div');
            buttonContainer.className = 'quiz-control-buttons';
            // Insert after the status element
            statusElement.parentElement.after(buttonContainer);
        }

        // Update buttons based on quiz status
        console.log("Updating buttons based on quiz status");
        console.log("Waiting, active, paused, completed");
        console.log("Data Status: ", data.status);
        switch(data.status) {
            case 'waiting':
                console.log("Waiting button container");
                buttonContainer.innerHTML = `
                    <button id="start-quiz-btn" onclick="quizGame.startQuiz()" class="btn btn-success">Start Quiz</button>
                `;
                break;
            case 'active':
                console.log("Active button container");
                buttonContainer.innerHTML = `
                    <button id="pause-quiz-btn" onclick="quizGame.pauseQuiz()" class="btn btn-warning">Pause Quiz</button>
                    <button id="end-quiz-btn" onclick="quizGame.endQuiz()" class="btn btn-danger">End Quiz</button>
                `;
                break;
            case 'paused':
                console.log("Paused button container");
                buttonContainer.innerHTML = `
                    <button id="resume-quiz-btn" onclick="quizGame.resumeQuiz()" class="btn btn-success">Resume Quiz</button>
                    <button id="end-quiz-btn" onclick="quizGame.endQuiz()" class="btn btn-danger">End Quiz</button>
                `;
                break;
            case 'completed':
                console.log("Completed button container");
                buttonContainer.innerHTML = `
                    <button disabled class="btn btn-secondary">Quiz Finished</button>
                `;
                break;
        }
        if (data.status === 'completed' && data.results) {
            this.showFinalResults(data.results);
        }
    }

    updateLeaderboard(data) {
        this.elements.leaderboard.innerHTML = data.map((player, index) => `
            <div class="leaderboard-item ${player.id === this.socket.id ? 'current-player' : ''}">
                <span class="rank">${index + 1}</span>
                <span class="name">${player.name}</span>
                <span class="score">${player.score}</span>
            </div>
        `).join('');
    }

    showFinalResults(results) {
        const container = this.elements.container;
        container.innerHTML = `
            <div class="final-results">
                <h2>Quiz Complete!</h2>
                <p>Your Final Score: ${this.score}</p>
                <p>Correct Answers: ${results.correct}</p>
                <p>Highest Streak: ${results.maxStreak}</p>
                <p>Average Time: ${results.avgTime.toFixed(2)}s</p>
                <button onclick="location.reload()">Play Again</button>
            </div>
        `;
    }

    getTimeTaken() {
        return this.timeLeft;
    }

    startQuiz() {
        console.log('Starting quiz...');
        onQuizStart(this.quiz.duration); // Start the timer with the quiz duration
        this.socket.emit('start_quiz', {
            quiz_id: this.quizId
        });
    }

    pauseQuiz() {
        console.log('Pausing quiz...');
        this.socket.emit('pause_quiz', {
            quiz_id: this.quizId
        });
        console.log('Emitting pause_quiz event for quiz ID:', this.quizId);
    }

    resumeQuiz() {
        console.log('Resuming quiz...');
        this.socket.emit('resume_quiz', {
            quiz_id: this.quizId
        });
        console.log('Emitting resume_quiz event for quiz ID:', this.quizId);
    }

    endQuiz() {
        console.log('Ending quiz...');
        this.socket.emit('end_quiz', {
            quiz_id: this.quizId
        });
    }

    copyQuizLink() {
        const linkElement = document.getElementById('quiz-link');
        if (linkElement) {
            navigator.clipboard.writeText(linkElement.textContent)
                .then(() => {
                    // Optional: Show feedback that link was copied
                    alert('Quiz link copied to clipboard!');
                })
                .catch(err => {
                    console.error('Failed to copy link:', err);
                });
        }
    }
}

export default QuizGame;
