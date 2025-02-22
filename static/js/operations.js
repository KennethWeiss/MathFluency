// Define and export the operations object
window.operations = {
    addition: {
        levels: {
            1: {
                description: "Single Digit - Basic addition of numbers from 0 to 9",
                sampleProblems: [
                    { problem: "3 + 4", answer: 7 },
                    { problem: "5 + 2", answer: 7 },
                    { problem: "6 + 3", answer: 9 },
                    { problem: "1 + 8", answer: 9 },
                    { problem: "4 + 4", answer: 8 },
                    { problem: "7 + 2", answer: 9 },
                    { problem: "0 + 9", answer: 9 },
                    { problem: "2 + 6", answer: 8 },
                    { problem: "3 + 5", answer: 8 },
                    { problem: "1 + 7", answer: 8 }
                ]
            },
            2: {
                description: "Double Digit - Addition of two-digit numbers (10-99)",
                sampleProblems: [
                    { problem: "23 + 45", answer: 68 },
                    { problem: "56 + 32", answer: 88 },
                    { problem: "78 + 21", answer: 99 },
                    { problem: "34 + 65", answer: 99 },
                    { problem: "12 + 87", answer: 99 },
                    { problem: "45 + 44", answer: 89 },
                    { problem: "67 + 22", answer: 89 },
                    { problem: "89 + 10", answer: 99 },
                    { problem: "55 + 33", answer: 88 },
                    { problem: "44 + 55", answer: 99 }
                ]
            },
            3: {
                description: "Make 10 - Problems that require making a total of 10",
                sampleProblems: [
                    { problem: "7 + __", answer: 3 },
                    { problem: "5 + __", answer: 5 },
                    { problem: "2 + __", answer: 8 },
                    { problem: "8 + __", answer: 2 },
                    { problem: "4 + __", answer: 6 },
                    { problem: "1 + __", answer: 9 },
                    { problem: "6 + __", answer: 4 },
                    { problem: "3 + __", answer: 7 },
                    { problem: "9 + __", answer: 1 },
                    { problem: "0 + __", answer: 10 }
                ]
            },
            4: {
                description: "Add to 100 - Addition problems that sum to 100",
                sampleProblems: [
                    { problem: "45 + 55", answer: 100 },
                    { problem: "67 + 33", answer: 100 },
                    { problem: "78 + 22", answer: 100 },
                    { problem: "89 + 11", answer: 100 },
                    { problem: "25 + 75", answer: 100 },
                    { problem: "40 + 60", answer: 100 },
                    { problem: "95 + 5", answer: 100 },
                    { problem: "82 + 18", answer: 100 },
                    { problem: "71 + 29", answer: 100 },
                    { problem: "63 + 37", answer: 100 }
                ]
            },
            5: {
                description: "Add to 1000 - Addition problems that sum to 1000",
                sampleProblems: [
                    { problem: "456 + 544", answer: 1000 },
                    { problem: "678 + 322", answer: 1000 },
                    { problem: "789 + 211", answer: 1000 },
                    { problem: "345 + 655", answer: 1000 },
                    { problem: "123 + 877", answer: 1000 },
                    { problem: "445 + 555", answer: 1000 },
                    { problem: "667 + 333", answer: 1000 },
                    { problem: "889 + 111", answer: 1000 },
                    { problem: "555 + 445", answer: 1000 },
                    { problem: "444 + 556", answer: 1000 }
                ]
            }
        }
    },
    multiplication: {
        levels: {
            1: {
                description: "×1 Table - Multiplication by 1",
                sampleProblems: [
                    { problem: "1 × 1", answer: 1 },
                    { problem: "1 × 2", answer: 2 },
                    { problem: "1 × 3", answer: 3 },
                    { problem: "1 × 4", answer: 4 },
                    { problem: "1 × 5", answer: 5 },
                    { problem: "1 × 6", answer: 6 },
                    { problem: "1 × 7", answer: 7 },
                    { problem: "1 × 8", answer: 8 },
                    { problem: "1 × 9", answer: 9 },
                    { problem: "1 × 10", answer: 10 }
                ]
            },
            2: {
                description: "×2 Table - Multiplication by 2",
                sampleProblems: [
                    { problem: "2 × 1", answer: 2 },
                    { problem: "2 × 2", answer: 4 },
                    { problem: "2 × 3", answer: 6 },
                    { problem: "2 × 4", answer: 8 },
                    { problem: "2 × 5", answer: 10 },
                    { problem: "2 × 6", answer: 12 },
                    { problem: "2 × 7", answer: 14 },
                    { problem: "2 × 8", answer: 16 },
                    { problem: "2 × 9", answer: 18 },
                    { problem: "2 × 10", answer: 20 }
                ]
            },
            3: {
                description: "×3 Table - Multiplication by 3",
                sampleProblems: [
                    { problem: "3 × 1", answer: 3 },
                    { problem: "3 × 2", answer: 6 },
                    { problem: "3 × 3", answer: 9 },
                    { problem: "3 × 4", answer: 12 },
                    { problem: "3 × 5", answer: 15 },
                    { problem: "3 × 6", answer: 18 },
                    { problem: "3 × 7", answer: 21 },
                    { problem: "3 × 8", answer: 24 },
                    { problem: "3 × 9", answer: 27 },
                    { problem: "3 × 10", answer: 30 }
                ]
            },
            4: {
                description: "×4 Table - Multiplication by 4",
                sampleProblems: [
                    { problem: "4 × 1", answer: 4 },
                    { problem: "4 × 2", answer: 8 },
                    { problem: "4 × 3", answer: 12 },
                    { problem: "4 × 4", answer: 16 },
                    { problem: "4 × 5", answer: 20 },
                    { problem: "4 × 6", answer: 24 },
                    { problem: "4 × 7", answer: 28 },
                    { problem: "4 × 8", answer: 32 },
                    { problem: "4 × 9", answer: 36 },
                    { problem: "4 × 10", answer: 40 }
                ]
            },
            5: {
                description: "×5 Table - Multiplication by 5",
                sampleProblems: [
                    { problem: "5 × 1", answer: 5 },
                    { problem: "5 × 2", answer: 10 },
                    { problem: "5 × 3", answer: 15 },
                    { problem: "5 × 4", answer: 20 },
                    { problem: "5 × 5", answer: 25 },
                    { problem: "5 × 6", answer: 30 },
                    { problem: "5 × 7", answer: 35 },
                    { problem: "5 × 8", answer: 40 },
                    { problem: "5 × 9", answer: 45 },
                    { problem: "5 × 10", answer: 50 }
                ]
            },
            6: {
                description: "×6 Table - Multiplication by 6",
                sampleProblems: [
                    { problem: "6 × 1", answer: 6 },
                    { problem: "6 × 2", answer: 12 },
                    { problem: "6 × 3", answer: 18 },
                    { problem: "6 × 4", answer: 24 },
                    { problem: "6 × 5", answer: 30 },
                    { problem: "6 × 6", answer: 36 },
                    { problem: "6 × 7", answer: 42 },
                    { problem: "6 × 8", answer: 48 },
                    { problem: "6 × 9", answer: 54 },
                    { problem: "6 × 10", answer: 60 }
                ]
            },
            7: {
                description: "×7 Table - Multiplication by 7",
                sampleProblems: [
                    { problem: "7 × 1", answer: 7 },
                    { problem: "7 × 2", answer: 14 },
                    { problem: "7 × 3", answer: 21 },
                    { problem: "7 × 4", answer: 28 },
                    { problem: "7 × 5", answer: 35 },
                    { problem: "7 × 6", answer: 42 },
                    { problem: "7 × 7", answer: 49 },
                    { problem: "7 × 8", answer: 56 },
                    { problem: "7 × 9", answer: 63 },
                    { problem: "7 × 10", answer: 70 }
                ]
            },
            8: {
                description: "×8 Table - Multiplication by 8",
                sampleProblems: [
                    { problem: "8 × 1", answer: 8 },
                    { problem: "8 × 2", answer: 16 },
                    { problem: "8 × 3", answer: 24 },
                    { problem: "8 × 4", answer: 32 },
                    { problem: "8 × 5", answer: 40 },
                    { problem: "8 × 6", answer: 48 },
                    { problem: "8 × 7", answer: 56 },
                    { problem: "8 × 8", answer: 64 },
                    { problem: "8 × 9", answer: 72 },
                    { problem: "8 × 10", answer: 80 }
                ]
            },
            9: {
                description: "×9 Table - Multiplication by 9",
                sampleProblems: [
                    { problem: "9 × 1", answer: 9 },
                    { problem: "9 × 2", answer: 18 },
                    { problem: "9 × 3", answer: 27 },
                    { problem: "9 × 4", answer: 36 },
                    { problem: "9 × 5", answer: 45 },
                    { problem: "9 × 6", answer: 54 },
                    { problem: "9 × 7", answer: 63 },
                    { problem: "9 × 8", answer: 72 },
                    { problem: "9 × 9", answer: 81 },
                    { problem: "9 × 10", answer: 90 }
                ]
            },
            10: {
                description: "×10 Table - Multiplication by 10",
                sampleProblems: [
                    { problem: "10 × 1", answer: 10 },
                    { problem: "10 × 2", answer: 20 },
                    { problem: "10 × 3", answer: 30 },
                    { problem: "10 × 4", answer: 40 },
                    { problem: "10 × 5", answer: 50 },
                    { problem: "10 × 6", answer: 60 },
                    { problem: "10 × 7", answer: 70 },
                    { problem: "10 × 8", answer: 80 },
                    { problem: "10 × 9", answer: 90 },
                    { problem: "10 × 10", answer: 100 }
                ]
            },
            11: {
                description: "×11 Table - Multiplication by 11",
                sampleProblems: [
                    { problem: "11 × 1", answer: 11 },
                    { problem: "11 × 2", answer: 22 },
                    { problem: "11 × 3", answer: 33 },
                    { problem: "11 × 4", answer: 44 },
                    { problem: "11 × 5", answer: 55 },
                    { problem: "11 × 6", answer: 66 },
                    { problem: "11 × 7", answer: 77 },
                    { problem: "11 × 8", answer: 88 },
                    { problem: "11 × 9", answer: 99 },
                    { problem: "11 × 10", answer: 110 }
                ]
            },
            12: {
                description: "×12 Table - Multiplication by 12",
                sampleProblems: [
                    { problem: "12 × 1", answer: 12 },
                    { problem: "12 × 2", answer: 24 },
                    { problem: "12 × 3", answer: 36 },
                    { problem: "12 × 4", answer: 48 },
                    { problem: "12 × 5", answer: 60 },
                    { problem: "12 × 6", answer: 72 },
                    { problem: "12 × 7", answer: 84 },
                    { problem: "12 × 8", answer: 96 },
                    { problem: "12 × 9", answer: 108 },
                    { problem: "12 × 10", answer: 120 }
                ]
            },
            'custom': {
                description: "Custom Multiplication - Define your own numbers",
                sampleProblems: [
                    { problem: "Custom × Custom", answer: "Variable" }
                ]
            }
        }
    }
};

// Helper functions for custom multiplication
function parseMultiplicandInput(input) {
    input = input.trim();
    if (!input) return [];

    // Check if it's a range (e.g., "1-10")
    if (input.includes('-')) {
        const [start, end] = input.split('-').map(num => parseInt(num.trim()));
        if (isNaN(start) || isNaN(end) || start > end) return [];
        return Array.from({length: end - start + 1}, (_, i) => start + i);
    }

    // Check if it's a comma-separated list (e.g., "2,3,5")
    return input.split(',')
        .map(num => parseInt(num.trim()))
        .filter(num => !isNaN(num));
}

function generateCustomSampleProblems(multiplicand1, multiplicand2) {
    const numbers1 = parseMultiplicandInput(multiplicand1);
    const numbers2 = parseMultiplicandInput(multiplicand2);
    
    if (!numbers1.length || !numbers2.length) return [];

    const problems = [];
    // Generate up to 10 sample problems
    for (let i = 0; i < Math.min(10, numbers1.length * numbers2.length); i++) {
        const num1 = numbers1[Math.floor(Math.random() * numbers1.length)];
        const num2 = numbers2[Math.floor(Math.random() * numbers2.length)];
        problems.push({
            problem: `${num1} × ${num2}`,
            answer: num1 * num2
        });
    }
    return problems;
}
