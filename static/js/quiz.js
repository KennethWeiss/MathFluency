document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('operation').addEventListener('change', function() {
        const operation = this.value;
        const levelSelect = document.getElementById('level');
        
        // Clear existing options
        levelSelect.innerHTML = '';

        let options = [];
        if (operation === 'addition') {
            options = [
                { value: 1, text: "1: Single Digit - Basic addition of numbers from 0 to 9." },
                { value: 2, text: "2: Double Digit - Addition of two-digit numbers (10-99)." },
                { value: 3, text: "3: Make 10 - Problems that require making a total of 10." },
                { value: 4, text: "4: Add to 100 - Addition problems that sum to 100." },
                { value: 5, text: "5: Add to 1000 - Addition problems that sum to 1000." }
            ];
        } else if (operation === 'multiplication') {
            options = [
                { value: 1, text: "1: ×1 Table - Multiplication by 1." },
                { value: 2, text: "2: ×2 Table - Multiplication by 2." },
                { value: 3, text: "3: ×3 Table - Multiplication by 3." },
                { value: 4, text: "4: ×4 Table - Multiplication by 4." },
                { value: 5, text: "5: ×5 Table - Multiplication by 5." },
                { value: 6, text: "6: ×6 Table - Multiplication by 6." },
                { value: 7, text: "7: ×7 Table - Multiplication by 7." },
                { value: 8, text: "8: ×8 Table - Multiplication by 8." },
                { value: 9, text: "9: ×9 Table - Multiplication by 9." },
                { value: 10, text: "10: ×10 Table - Multiplication by 10." },
                { value: 11, text: "11: ×11 Table - Multiplication by 11." },
                { value: 12, text: "12: ×12 Table - Multiplication by 12." }
            ];
        }

        // Populate the level select with new options
        options.forEach(option => {
            const newOption = document.createElement('option');
            newOption.value = option.value;
            newOption.textContent = option.text;
            levelSelect.appendChild(newOption);
        });
    });
});
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('operation').addEventListener('change', function() {
        const operation = this.value;
        const levelSelect = document.getElementById('level');
        
        // Clear existing options
        levelSelect.innerHTML = '';

        let options = [];
        if (operation === 'addition') {
            options = [
                { value: 1, text: "1: Single Digit - Basic addition of numbers from 0 to 9." },
                { value: 2, text: "2: Double Digit - Addition of two-digit numbers (10-99)." },
                { value: 3, text: "3: Make 10 - Problems that require making a total of 10." },
                { value: 4, text: "4: Add to 100 - Addition problems that sum to 100." },
                { value: 5, text: "5: Add to 1000 - Addition problems that sum to 1000." }
            ];
        } else if (operation === 'multiplication') {
            options = [
                { value: 1, text: "1: ×1 Table - Multiplication by 1." },
                { value: 2, text: "2: ×2 Table - Multiplication by 2." },
                { value: 3, text: "3: ×3 Table - Multiplication by 3." },
                { value: 4, text: "4: ×4 Table - Multiplication by 4." },
                { value: 5, text: "5: ×5 Table - Multiplication by 5." },
                { value: 6, text: "6: ×6 Table - Multiplication by 6." },
                { value: 7, text: "7: ×7 Table - Multiplication by 7." },
                { value: 8, text: "8: ×8 Table - Multiplication by 8." },
                { value: 9, text: "9: ×9 Table - Multiplication by 9." },
                { value: 10, text: "10: ×10 Table - Multiplication by 10." },
                { value: 11, text: "11: ×11 Table - Multiplication by 11." },
                { value: 12, text: "12: ×12 Table - Multiplication by 12." }
            ];
        }

        // Populate the level select with new options
        options.forEach(option => {
            const newOption = document.createElement('option');
            newOption.value = option.value;
            newOption.textContent = option.text;
            levelSelect.appendChild(newOption);
        });
    });
});
    constructor(quizId, isTeacher = false) {
        this.quizId = quizId;
        this.isTeacher = isTeacher;
        this.score = 0;
        this.streak = 0;
        this.timer = null;
        this.timeLeft = 0;
        this.currentProblem = null;
        this.currentAnswer = null;

        // Setup socket with correct port
        this.socket = io({
            transports: ['websocket'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            path: '/socket.io',
            port: 5001,
            secure: false
        });

        // Cache elements that exist in this view
        this.elements = this.cacheElements();
        
        // Setup socket listeners
        this.setupSocketListeners();

        // Set initial button state if teacher
        if (this.isTeacher) {
            // Get initial quiz status from the page
            const statusElement = document.getElementById('quiz-status');
            if (statusElement) {
                const initialStatus = statusElement.textContent.trim().toLowerCase();
                console.log('Initial quiz status:', initialStatus);
                this.updateButtonVisibility(initialStatus);
            } else {
                console.warn('Quiz status element not found');
            }
        }
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

    restartQuiz() {
        console.log('Restarting quiz...');
        this.socket.emit('restart_quiz', { quiz_id: this.quizId });
    }

    submitAnswer(answer) {
        console.log('Submitting answer:', answer);
        this.socket.emit('submit_answer', {
            quiz_id: this.quizId,
            answer: answer,
            correct_answer: this.currentAnswer,
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

    updateLeaderboard(leaderboard) {
        const leaderboardElement = document.getElementById('leaderboard'); // Assuming there's an element with this ID
        leaderboardElement.innerHTML = ''; // Clear existing leaderboard

        leaderboard.forEach(entry => {
            const listItem = document.createElement('li');
            listItem.textContent = `${entry.username}: ${entry.score}`;
            leaderboardElement.appendChild(listItem);
        });
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.socket.emit('join_quiz', {
                quiz_id: this.quizId,
                is_teacher: this.isTeacher
            });
        });

        this.socket.on('quiz_status_changed', (data) => {
            console.log('Quiz status changed:', data);
            if (data.quiz_id == this.quizId) {
                if (this.elements.status) {
                    this.elements.status.textContent = data.status;
                }
                this.updateScreens(data.status);
                this.updateButtonVisibility(data.status);
            }
        });

        this.socket.on('new_problem', (data) => {
            console.log('New problem received:', data);
            if (data.quiz_id == this.quizId) {
                this.displayProblem(data.problem);
                this.currentAnswer = data.answer;
            }
        });

        this.socket.on('answer_feedback', (data) => {
            console.log('Answer feedback received:', data);
            this.showFeedback(data.correct);
        });

        this.socket.on('score_updated', (data) => {
            console.log('Score updated:', data);
            if (this.elements.score) {
                this.elements.score.textContent = data.score;
            }
        });

        this.socket.on('quiz_ended', (data) => {
            console.log('Quiz ended:', data);
            if (data.quiz_id == this.quizId) {
                if (this.elements.status) {
                    this.elements.status.textContent = 'finished';
                }
                this.updateScreens('finished');
                this.updateButtonVisibility('finished');

                // Display final scores if provided
                if (data.scores) {
                    console.log('Final scores:', data.scores);
                    // You can add UI here to show final scores
                }
            }
        });

        this.socket.on('update_leaderboard', (data) => {
            console.log('Leaderboard updated:', data);
            this.updateLeaderboard(data.leaderboard);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
        });
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.socket.emit('join_quiz', {
                quiz_id: this.quizId,
                is_teacher: this.isTeacher
            });
        });

        this.socket.on('quiz_status_changed', (data) => {
            console.log('Quiz status changed:', data);
            if (data.quiz_id == this.quizId) {
                if (this.elements.status) {
                    this.elements.status.textContent = data.status;
                }
                this.updateScreens(data.status);
                this.updateButtonVisibility(data.status);
            }
        });

        this.socket.on('new_problem', (data) => {
            console.log('New problem received:', data);
            if (data.quiz_id == this.quizId) {
                this.displayProblem(data.problem);
                this.currentAnswer = data.answer;
            }
        });

        this.socket.on('answer_feedback', (data) => {
            console.log('Answer feedback received:', data);
            this.showFeedback(data.correct);
        });

        this.socket.on('score_updated', (data) => {
            console.log('Score updated:', data);
            if (this.elements.score) {
                this.elements.score.textContent = data.score;
            }
        });

        this.socket.on('quiz_ended', (data) => {
            console.log('Quiz ended:', data);
            if (data.quiz_id == this.quizId) {
                if (this.elements.status) {
                    this.elements.status.textContent = 'finished';
                }
                this.updateScreens('finished');
                this.updateButtonVisibility('finished');

                // Display final scores if provided
                if (data.scores) {
                    console.log('Final scores:', data.scores);
                    // You can add UI here to show final scores
                }
            }
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
        });
    }

    updateButtonVisibility(status) {
        // Only handle buttons if this is the teacher view
        if (!this.isTeacher) return;

        // Clean up status text by removing whitespace and converting to lowercase
        status = status.trim().toLowerCase();
        console.log('Updating button visibility for cleaned status:', status);

        // Get all possible buttons
        const buttons = {
            start: document.getElementById('start-quiz-btn'),
            pause: document.getElementById('pause-quiz-btn'),
            resume: document.getElementById('resume-quiz-btn'),
            end: document.getElementById('end-quiz-btn'),
            restart: document.getElementById('restart-quiz-btn')
        };

        // Log which buttons were found
        Object.entries(buttons).forEach(([name, button]) => {
            console.log(`${name} button found:`, !!button);
        });

        // Hide all buttons first
        Object.values(buttons).forEach(button => {
            if (button) {
                button.style.display = 'none';
                button.disabled = false; // Reset disabled state
            }
        });

        console.log('Showing buttons for status:', status);
        
        // Show appropriate buttons based on status
        switch (status) {
            case 'waiting':
                console.log('Showing start button');
                if (buttons.start) {
                    buttons.start.style.display = 'inline-block';
                }
                break;

            case 'active':
                console.log('Showing pause and end buttons');
                if (buttons.pause) {
                    buttons.pause.style.display = 'inline-block';
                }
                if (buttons.end) {
                    buttons.end.style.display = 'inline-block';
                }
                break;

            case 'paused':
                console.log('Showing resume and end buttons');
                if (buttons.resume) {
                    buttons.resume.style.display = 'inline-block';
                }
                if (buttons.end) {
                    buttons.end.style.display = 'inline-block';
                }
                break;

            case 'finished':
                console.log('Showing restart button');
                if (buttons.restart) {
                    buttons.restart.style.display = 'inline-block';
                }
                break;

            default:
                console.log('Unknown status:', status);
                break;
        }

        // Log final button states
        Object.entries(buttons).forEach(([name, button]) => {
            if (button) {
                console.log(`${name} button final state:`, {
                    display: button.style.display,
                    disabled: button.disabled,
                    visible: button.offsetParent !== null
                });
            }
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
    }
}
