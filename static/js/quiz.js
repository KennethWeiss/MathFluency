// Quiz Game Logic
class QuizGame {
    constructor(quizId, isTeacher = false) {
        this.quizId = quizId;
        this.isTeacher = isTeacher;
        this.socket = io();
        this.score = 0;
        this.streak = 0;
        this.timer = null;
        this.timeLeft = 0;
        this.elements = this.cacheElements();
        this.setupSocketListeners();
    }

    cacheElements() {
        return {
            problem: document.getElementById('problem'),
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
                console.log('New problem received');
                this.displayProblem(data.problem);
                this.startTimer(data.timeLimit);
            },
            'answer_result': (data) => {
                console.log('Answer result received');
                this.handleAnswerResult(data);
            },
            'quiz_status_changed': (data) => {
                console.log('Quiz status changed:', data.status);
                this.updateQuizStatus(data);
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

        // Initial join
        socketEvents['join_quiz']();
    }

    submitAnswer(answer) {
        if (!this.timer) return; // Don't submit if timer is not running

        clearInterval(this.timer);
        this.socket.emit('submit_answer', {
            quiz_id: this.quizId,
            answer: answer,
            time_taken: this.getTimeTaken()
        });
    }

    displayProblem(problem) {
        console.log('Displaying problem:', problem);
        this.elements.problem.textContent = problem;
        this.elements.answer.value = '';
        this.elements.answer.focus();
    }

    startTimer(duration) {
        this.timeLeft = duration;
        if (this.timer) clearInterval(this.timer);

        this.timer = setInterval(() => {
            this.elements.timer.textContent = this.timeLeft;
            if (this.timeLeft <= 0) {
                clearInterval(this.timer);
                this.submitAnswer(null);
            }
            this.timeLeft--;
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
        console.log(data.status);
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
        switch(data.status) {
            case 'waiting':
                buttonContainer.innerHTML = `
                    <button id="start-quiz-btn" onclick="quizGame.startQuiz()" class="btn btn-success">Start Quiz</button>
                `;
                break;
            case 'active':
                buttonContainer.innerHTML = `
                    <button id="pause-quiz-btn" onclick="quizGame.pauseQuiz()" class="btn btn-warning">Pause Quiz</button>
                    <button id="end-quiz-btn" onclick="quizGame.endQuiz()" class="btn btn-danger">End Quiz</button>
                `;
                break;
            case 'paused':
                buttonContainer.innerHTML = `
                    <button id="resume-quiz-btn" onclick="quizGame.resumeQuiz()" class="btn btn-success">Resume Quiz</button>
                    <button id="end-quiz-btn" onclick="quizGame.endQuiz()" class="btn btn-danger">End Quiz</button>
                `;
                break;
            case 'completed':
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
        this.socket.emit('start_quiz', {
            quiz_id: this.quizId
        });
    }

    pauseQuiz() {
        console.log('Pausing quiz...');
        this.socket.emit('pause_quiz', {
            quiz_id: this.quizId
        });
    }

    resumeQuiz() {
        console.log('Resuming quiz...');
        this.socket.emit('resume_quiz', {
            quiz_id: this.quizId
        });
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
