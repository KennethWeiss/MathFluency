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
        this.setupSocketListeners();
    }

    setupSocketListeners() {
        // Join quiz room
        console.log('Attempting to join quiz...')
        this.socket.emit('join_quiz', { 
            quiz_id: this.quizId,
            is_teacher: this.isTeacher 
        });

        // Listen for new problems
        console.log('Setting up new_problem listener...')
        this.socket.on('new_problem', (data) => {
            this.displayProblem(data.problem);
            this.startTimer(data.timeLimit);
        });

        // Listen for answer results
        console.log('Setting up answer_result listener...')
        this.socket.on('answer_result', (data) => {
            this.handleAnswerResult(data);
        });

        // Listen for quiz status updates
        console.log('Setting up quiz_status listener...')
        this.socket.on('quiz_status', (data) => {
            this.updateQuizStatus(data);
        });

        // Listen for leaderboard updates
        console.log('Setting up leaderboard_update listener...')
        this.socket.on('leaderboard_update', (data) => {
            this.updateLeaderboard(data);
        });
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
        const problemElement = document.getElementById('problem');
        problemElement.textContent = problem;
        
        // Clear previous answer
        const answerInput = document.getElementById('answer');
        answerInput.value = '';
        answerInput.focus();
    }

    startTimer(duration) {
        this.timeLeft = duration;
        const timerElement = document.getElementById('timer');

        if (this.timer) clearInterval(this.timer);

        this.timer = setInterval(() => {
            timerElement.textContent = this.timeLeft;
            if (this.timeLeft <= 0) {
                clearInterval(this.timer);
                this.submitAnswer(null); // Submit null for timeout
            }
            this.timeLeft--;
        }, 1000);
    }

    handleAnswerResult(data) {
        console.log('Handling answer result:', data);
        const { correct, points, streak } = data;
        this.score += points;
        this.streak = streak;

        // Update UI
        document.getElementById('score').textContent = this.score;
        document.getElementById('streak').textContent = this.streak;

        // Show feedback
        this.showFeedback(correct);
    }

    showFeedback(correct) {
        const feedback = document.getElementById('feedback');
        feedback.textContent = correct ? '✓ Correct!' : '✗ Wrong!';
        feedback.className = correct ? 'feedback correct' : 'feedback wrong';
        
        // Animate feedback
        feedback.style.animation = 'none';
        feedback.offsetHeight; // Trigger reflow
        feedback.style.animation = 'feedbackPop 0.5s';
    }

    updateQuizStatus(data) {
        const statusElement = document.getElementById('quiz-status');
        console.log(data.status);
        console.log("Status Element: ", statusElement);
        statusElement.textContent = data.status;

        if (data.status === 'completed') {
            this.showFinalResults(data.results);
        }
    }

    updateLeaderboard(data) {
        const leaderboard = document.getElementById('leaderboard');
        leaderboard.innerHTML = data.map((player, index) => `
            <div class="leaderboard-item ${player.id === this.socket.id ? 'current-player' : ''}">
                <span class="rank">${index + 1}</span>
                <span class="name">${player.name}</span>
                <span class="score">${player.score}</span>
            </div>
        `).join('');
    }

    showFinalResults(results) {
        const container = document.getElementById('quiz-container');
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
}

// CSS Animations
const style = document.createElement('style');
style.textContent = `
    @keyframes feedbackPop {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }

    .feedback {
        font-size: 1.5em;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }

    .feedback.correct {
        color: #28a745;
    }

    .feedback.wrong {
        color: #dc3545;
    }

    .leaderboard-item {
        display: flex;
        justify-content: space-between;
        padding: 5px 10px;
        margin: 2px 0;
        border-radius: 4px;
    }

    .current-player {
        background-color: #e9ecef;
        font-weight: bold;
    }
`;
document.head.appendChild(style);
