#!/usr/bin/env python3

import json


class QuizHTMLGenerator:
    def generate_quiz_html(self, questions):
        """Generate HTML content for quiz with one question per page"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FancyGit Quiz</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .submit-btn-top {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: linear-gradient(45deg, #dc3545, #c82333);
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 0.9em;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }}
        
        .submit-btn-top:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(220, 53, 69, 0.4);
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.3);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 20px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4ECDC4, #44A08D);
            width: 5%;
            transition: width 0.3s ease;
        }}
        
        .quiz-content {{
            padding: 30px;
            min-height: 400px;
        }}
        
        .question {{
            display: none;
            animation: fadeIn 0.3s ease-in;
        }}
        
        .question.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .question h3 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.3em;
            line-height: 1.4;
        }}
        
        .options {{
            list-style: none;
        }}
        
        .options li {{
            margin-bottom: 15px;
        }}
        
        .options label {{
            display: flex;
            align-items: flex-start;
            padding: 15px;
            background: white;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid #e9ecef;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .options label:hover {{
            background: #f8f9fa;
            border-color: #4ECDC4;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .options input[type="radio"] {{
            margin-right: 15px;
            margin-top: 2px;
            width: 20px;
            height: 20px;
        }}
        
        .options input[type="radio"]:checked + span {{
            color: #2c3e50;
            font-weight: 600;
        }}
        
        .options input[type="radio"]:checked ~ label {{
            background: #e8f4f8;
            border-color: #4ECDC4;
        }}
        
        .level-badge {{
            display: inline-block;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            margin-left: 10px;
        }}
        
        .level-beginner {{ background: #d4edda; color: #155724; }}
        .level-intermediate {{ background: #fff3cd; color: #856404; }}
        .level-advanced {{ background: #cce5ff; color: #004085; }}
        .level-challenging {{ background: #f8d7da; color: #721c24; }}
        
        .type-badge {{
            display: inline-block;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            margin-left: 5px;
        }}
        
        .type-theory {{ background: #e2e3e5; color: #383d41; }}
        .type-scenario {{ background: #d1ecf1; color: #0c5460; }}
        
        .navigation {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 30px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }}
        
        .question-squares {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: center;
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }}
        
        .question-square {{
            width: 35px;
            height: 35px;
            border-radius: 8px;
            border: 2px solid #dee2e6;
            background: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            font-weight: 600;
            color: #6c757d;
            transition: all 0.3s ease;
        }}
        
        .question-square:hover {{
            border-color: #4ECDC4;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .question-square.active {{
            background: #4ECDC4;
            color: white;
            border-color: #4ECDC4;
        }}
        
        .question-square.completed {{
            background: #28a745;
            color: white;
            border-color: #28a745;
        }}
        
        .question-square.unanswered {{
            background: white;
            color: #6c757d;
            border-color: #dee2e6;
        }}
        
        .btn {{
            background: linear-gradient(45deg, #4ECDC4, #44A08D);
            color: white;
            border: none;
            padding: 12px 25px;
            font-size: 1em;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 120px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(78, 205, 196, 0.4);
        }}
        
        .btn:disabled {{
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}
        
        .btn-secondary {{
            background: linear-gradient(45deg, #FF6B6B, #FF8E53);
        }}
        
        .btn-danger {{
            background: linear-gradient(45deg, #dc3545, #c82333);
        }}
        
        .question-counter {{
            font-size: 1.1em;
            color: #6c757d;
            font-weight: 600;
        }}
        
        .results {{
            padding: 30px;
            text-align: center;
            display: none;
        }}
        
        .score {{
            font-size: 3em;
            font-weight: bold;
            margin: 20px 0;
        }}
        
        .score-excellent {{ color: #28a745; }}
        .score-good {{ color: #007bff; }}
        .score-average {{ color: #ffc107; }}
        .score-poor {{ color: #dc3545; }}
        
        .answer-review {{
            text-align: left;
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .answer-item {{
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 8px;
        }}
        
        .answer-correct {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        
        .answer-incorrect {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        
        .unanswered-warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }}
        
        .unanswered-questions {{
            font-weight: bold;
        }}
        
        .ordering-options {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        
        .ordering-item {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            cursor: move;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            position: relative;
        }}
        
        .ordering-item:hover {{
            border-color: #4ECDC4;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .ordering-item.dragging {{
            opacity: 0.5;
            transform: rotate(5deg);
        }}
        
        .ordering-item.drag-over {{
            border-color: #007bff;
            background: #e8f4f8;
        }}
        
        .order-number {{
            background: #4ECDC4;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
            flex-shrink: 0;
        }}
        
        .order-text {{
            flex: 1;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
        }}
        
        .drag-handle {{
            color: #6c757d;
            margin-left: 10px;
            font-size: 1.2em;
            cursor: grab;
        }}
        
        .drag-handle:active {{
            cursor: grabbing;
        }}
        
        .ordering-instructions {{
            background: #e8f4f8;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 0.9em;
        }}
        
        .confirm-order-btn {{
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            border: none;
            padding: 12px 25px;
            font-size: 1em;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .confirm-order-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(40, 167, 69, 0.4);
        }}
        
        .confirm-order-btn.confirmed {{
            background: linear-gradient(45deg, #6c757d, #5a6268);
            cursor: default;
        }}
        
        .confirm-order-btn.confirmed:hover {{
            transform: none;
            box-shadow: none;
        }}
        
        .ordering-options.completed {{
            position: relative;
        }}
        
        .ordering-options.completed::before {{
            content: '';
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 1.5em;
            color: #28a745;
            background: white;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .ordering-options.completed .ordering-item {{
            background: #d4edda;
            border-color: #28a745;
            color: #155724;
            cursor: not-allowed;
            opacity: 0.8;
        }}
        
        .ordering-options.completed .ordering-item:hover {{
            border-color: #20c997;
            background: #c3e6cb;
            transform: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .ordering-options.completed .ordering-item .drag-handle {{
            color: #6c757d;
            cursor: not-allowed;
            opacity: 0.5;
        }}
        
        .ordering-options.completed .order-number {{
            background: #28a745;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 FancyGit Quiz</h1>
            <p>Test your Git knowledge with {len(questions)} questions</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progress"></div>
            </div>
        </div>
        
        <div class="unanswered-warning" id="unanswered-warning">
            <strong>⚠️ Please answer all questions before submitting!</strong><br>
            <span class="unanswered-questions" id="unanswered-questions"></span>
        </div>
        
        <div id="quiz-container" class="quiz-content">
"""
        
        # Add questions
        for i, q in enumerate(questions, 1):
            level_class = f"level-{q.get('level', 'beginner')}"
            type_class = f"type-{q.get('type', 'theory')}"
            
            html += f"""
            <div class="question {'active' if i == 1 else ''}" data-question="{i}" data-answer="{q.get('answer', '')}" data-type="{q.get('type', 'theory')}" data-options='{json.dumps(q.get('options', []))}'>
                <h3>
                    {i}. {q.get('q', '')}
                    <span class="level-badge {level_class}">{q.get('level', 'beginner')}</span>
                    <span class="type-badge {type_class}">{q.get('type', 'theory')}</span>
                </h3>
"""
            
            if q.get('type') == 'ordering':
                html += f"""
                <div class="ordering-instructions">
                    📝 <strong>Drag and drop the steps to arrange them in the correct order:</strong>
                </div>
                <ul class="ordering-options" id="ordering-{i}">
"""
                
                options = q.get('options', [])
                # Shuffle options for ordering questions
                import random
                shuffled_options = options[:]
                random.shuffle(shuffled_options)
                
                for j, option in enumerate(shuffled_options):
                    html += f"""
                    <li class="ordering-item" draggable="true" data-option="{chr(65 + options.index(option))}">
                        <span class="order-number">{j + 1}</span>
                        <span class="order-text">{option}</span>
                        <span class="drag-handle">⋮⋮</span>
                    </li>
"""
                
                html += f"""
                </ul>
                <button class="confirm-order-btn" id="confirm-btn-{i}" onclick="confirmOrder({i})">
                    <span>✓</span>
                    <span>Confirm Order</span>
                </button>
"""
            else:
                # Regular MCQ questions
                html += """
                <ul class="options">
"""
                
                options = q.get('options', [])
                for j, option in enumerate(options):
                    option_letter = chr(65 + j)  # A, B, C, D
                    html += f"""
                    <li>
                        <label>
                            <input type="radio" name="q{i}" value="{option_letter}">
                            <span>{option_letter}. {option}</span>
                        </label>
                    </li>
"""
                
                html += """
                </ul>
"""
            
            html += """
            </div>
"""
        
        html += f"""
        </div>
        
        <div class="navigation">
            <button class="btn" id="prev-btn" onclick="previousQuestion()" disabled>Previous</button>
            <span class="question-counter" id="question-counter">Question 1 of {len(questions)}</span>
            <button class="btn" id="next-btn" onclick="nextQuestion()">Next</button>
        </div>
        
        <div class="question-squares" id="question-squares">
            <!-- Question squares will be generated by JavaScript -->
        </div>
        
        <div id="results" class="results">
            <h2>🎉 Quiz Complete!</h2>
            <div id="score" class="score"></div>
            <div id="score-message"></div>
            <div id="answer-review" class="answer-review"></div>
            <div id="result-buttons">
                <button class="btn btn-secondary" id="retry-failed-btn" onclick="retryFailedQuestions()" style="display: none;">Retry Failed Questions</button>
                <button class="btn" onclick="generateNewQuestions()">Generate New Questions</button>
            </div>
        </div>

        <div id="retry-results" class="results" style="display: none;">
            <h2>🔄 Retry Complete!</h2>
            <div id="retry-summary" class="score"></div>
            <div id="retry-message"></div>
            <div id="retry-review" class="answer-review"></div>
            <div id="retry-result-buttons">
                <button class="btn btn-secondary" id="retry-remaining-btn" onclick="retryFailedQuestions()">Retry Remaining Failed Questions</button>
                <button class="btn" onclick="backToOriginalResults()">Back to Original Results</button>
            </div>
        </div>
    </div>

    <script>
        let currentQuestion = 1;
        const totalQuestions = {len(questions)};
        const userAnswers = {{}};
        
        // Drag and drop functionality for ordering questions
        let draggedElement = null;
        
        function initializeOrderingQuestions() {{
            document.querySelectorAll('.ordering-options').forEach(container => {{
                container.addEventListener('dragstart', handleDragStart);
                container.addEventListener('dragover', handleDragOver);
                container.addEventListener('drop', handleDrop);
                container.addEventListener('dragend', handleDragEnd);
            }});
        }}
        
        function handleDragStart(e) {{
            if (e.target.classList.contains('ordering-item')) {{
                // Check if the container is completed (locked)
                const container = e.target.closest('.ordering-options');
                if (container && container.classList.contains('completed')) {{
                    e.preventDefault();
                    return false;
                }}
                
                draggedElement = e.target;
                e.target.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', e.target.innerHTML);
            }}
        }}
        
        function handleDragOver(e) {{
            if (e.preventDefault) {{
                e.preventDefault();
            }}
            
            // Check if the container is completed (locked)
            if (e.currentTarget.classList.contains('completed')) {{
                return false;
            }}
            
            e.dataTransfer.dropEffect = 'move';
            
            const afterElement = getDragAfterElement(e.currentTarget, e.clientY);
            const dragging = document.querySelector('.dragging');
            
            if (afterElement == null) {{
                e.currentTarget.appendChild(dragging);
            }} else {{
                e.currentTarget.insertBefore(dragging, afterElement);
            }}
            
            return false;
        }}
        
        function handleDrop(e) {{
            if (e.stopPropagation) {{
                e.stopPropagation();
            }}
            
            updateOrderNumbers();
            return false;
        }}
        
        function handleDragEnd(e) {{
            document.querySelectorAll('.ordering-item').forEach(item => {{
                item.classList.remove('dragging');
                item.classList.remove('drag-over');
            }});
        }}
        
        function getDragAfterElement(container, y) {{
            const draggableElements = [...container.querySelectorAll('.ordering-item:not(.dragging)')];
            
            return draggableElements.reduce((closest, child) => {{
                const box = child.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;
                
                if (offset < 0 && offset > closest.offset) {{
                    return {{ offset: offset, element: child }};
                }} else {{
                    return closest;
                }}
            }}, {{ offset: Number.NEGATIVE_INFINITY }}).element;
        }}
        
        function updateOrderNumbers() {{
            document.querySelectorAll('.ordering-options').forEach(container => {{
                const items = container.querySelectorAll('.ordering-item');
                items.forEach((item, index) => {{
                    const orderNumber = item.querySelector('.order-number');
                    orderNumber.textContent = index + 1;
                }});
            }});
        }}
        
        function getOrderingAnswer(questionNum) {{
            const container = document.getElementById(`ordering-${{questionNum}}`);
            if (!container) return '';
            
            const items = container.querySelectorAll('.ordering-item');
            let answer = '';
            items.forEach(item => {{
                answer += item.dataset.option;
            }});
            return answer;
        }}
        
        function confirmOrder(questionNum) {{
            const container = document.getElementById(`ordering-${{questionNum}}`);
            const button = document.getElementById(`confirm-btn-${{questionNum}}`);
            
            if (!container || !button) {{
                console.error('Container or button not found');
                return;
            }}
            
            const items = container.querySelectorAll('.ordering-item');
            
            if (container.classList.contains('completed')) {{
                // Unconfirm - remove completed state and re-enable dragging
                container.classList.remove('completed');
                button.classList.remove('confirmed');
                button.innerHTML = '<span>✓</span><span>Confirm Order</span>';
                
                // Re-enable dragging
                items.forEach(item => {{
                    item.draggable = true;
                    item.style.cursor = 'move';
                }});
            }} else {{
                // Confirm - add completed state and disable dragging
                container.classList.add('completed');
                button.classList.add('confirmed');
                button.innerHTML = '<span>↺</span><span>Unconfirm Order</span>';
                
                // Disable dragging
                items.forEach(item => {{
                    item.draggable = false;
                    item.style.cursor = 'default';
                }});
            }}
            
            // Update square states to reflect completion
            updateSquareStates();
        }}
        
        // Make sure the function is globally accessible
        window.confirmOrder = confirmOrder;
        
        function initializeQuestionSquares() {{
            const squaresContainer = document.getElementById('question-squares');
            squaresContainer.innerHTML = '';
            
            for (let i = 1; i <= totalQuestions; i++) {{
                const square = document.createElement('div');
                square.className = 'question-square unanswered';
                square.textContent = i;
                square.onclick = () => goToQuestion(i);
                square.id = `square-${{i}}`;
                squaresContainer.appendChild(square);
            }}
            
            updateSquareStates();
        }}
        
        function updateSquareStates() {{
            for (let i = 1; i <= totalQuestions; i++) {{
                const square = document.getElementById(`square-${{i}}`);
                const question = document.querySelector(`[data-question="${{i}}"]`);
                const questionType = question.dataset.type;
                
                let isCompleted = false;
                
                if (questionType === 'ordering') {{
                    // Check if ordering question has been confirmed
                    const container = document.getElementById(`ordering-${{i}}`);
                    isCompleted = container && container.classList.contains('completed');
                }} else {{
                    // Check MCQ questions
                    const selectedInput = document.querySelector(`input[name="q${{i}}"]:checked`);
                    isCompleted = !!selectedInput;
                }}
                
                square.classList.remove('active', 'completed', 'unanswered');
                
                if (i === currentQuestion) {{
                    square.classList.add('active');
                }} else if (isCompleted) {{
                    square.classList.add('completed');
                }} else {{
                    square.classList.add('unanswered');
                }}
            }}
        }}
        
        function goToQuestion(questionNum) {{
            showQuestion(questionNum);
        }}
        
        function showQuestion(questionNum) {{
            // Hide all questions
            document.querySelectorAll('.question').forEach(q => q.classList.remove('active'));
            
            // Show current question (only if it's visible in current mode)
            const questionToShow = document.querySelector(`[data-question="${{questionNum}}"]`);
            if (questionToShow.style.display !== 'none') {{
                questionToShow.classList.add('active');
            }}
            
            // Update navigation
            if (window.retryMode) {{
                updateRetryProgress();
            }} else {{
                document.getElementById('prev-btn').disabled = questionNum === 1;
                document.getElementById('next-btn').textContent = questionNum === totalQuestions ? 'Submit' : 'Next';
                document.getElementById('next-btn').className = questionNum === totalQuestions ? 'btn btn-danger' : 'btn';
                document.getElementById('question-counter').textContent = `Question ${{questionNum}} of ${{totalQuestions}}`;
                
                // Update progress bar
                const progress = (questionNum / totalQuestions) * 100;
                document.getElementById('progress').style.width = `${{progress}}%`;
            }}
            
            currentQuestion = questionNum;
            updateSquareStates();
        }}
        
        function nextQuestion() {{
            if (window.retryMode) {{
                if (currentRetryQuestion < window.retryQuestions.length) {{
                    showRetryQuestion(currentRetryQuestion + 1);
                }} else {{
                    // Last retry question, submit retry
                    submitRetryQuiz();
                }}
            }} else {{
                if (currentQuestion === totalQuestions) {{
                    submitQuiz();
                }} else {{
                    showQuestion(currentQuestion + 1);
                }}
            }}
        }}
        
        function previousQuestion() {{
            if (window.retryMode) {{
                if (currentRetryQuestion > 1) {{
                    showRetryQuestion(currentRetryQuestion - 1);
                }}
            }} else {{
                if (currentQuestion > 1) {{
                    showQuestion(currentQuestion - 1);
                }}
            }}
        }}
        
        function submitRetryQuiz() {{
            // Validate retry quiz
            const unansweredRetryQuestions = [];
            
            for (let i = 1; i <= window.retryQuestions.length; i++) {{
                const selectedInput = document.querySelector(`input[name="q${{i}}"]:checked`);
                if (!selectedInput) {{
                    unansweredRetryQuestions.push(i);
                }}
            }}
            
            if (unansweredRetryQuestions.length > 0) {{
                // Show warning message instead of alert
                const warningDiv = document.createElement('div');
                warningDiv.className = 'unanswered-warning';
                warningDiv.style.display = 'block';
                warningDiv.innerHTML = `
                    <strong>⚠️ Please answer all retry questions before submitting!</strong><br>
                    <span class="unanswered-questions">Unanswered retry questions: ${{unansweredRetryQuestions.join(', ')}}</span>
                `;
                
                // Insert warning at the top of quiz container
                const quizContainer = document.getElementById('quiz-container');
                quizContainer.insertBefore(warningDiv, quizContainer.firstChild);
                
                // Navigate to first unanswered question
                if (unansweredRetryQuestions.length > 0) {{
                    showRetryQuestion(unansweredRetryQuestions[0]);
                }}
                
                // Remove warning after 3 seconds
                setTimeout(() => {{
                    if (warningDiv.parentNode) {{
                        warningDiv.parentNode.removeChild(warningDiv);
                    }}
                }}, 3000);
                
                return;
            }}
            
            // Check if retry questions are now correct
            let retryCorrect = 0;
            let retryReviewHtml = '<h3>🔄 Retry Results</h3>';
            const remainingFailedQuestions = [];
            
            for (let i = 1; i <= window.retryQuestions.length; i++) {{
                const originalNum = window.retryQuestions[i - 1];
                const question = document.querySelector(`[data-question="${{originalNum}}"]`);
                const correctAnswer = question.dataset.answer;
                const selectedInput = document.querySelector(`input[name="q${{i}}"]:checked`);
                const selectedAnswer = selectedInput ? selectedInput.value : '';
                
                const isCorrect = selectedAnswer === correctAnswer;
                if (isCorrect) {{
                    retryCorrect++;
                }} else {{
                    remainingFailedQuestions.push(originalNum);
                }}
                
                // Add to retry review
                const questionHeading = question.querySelector('h3');
                const questionText = questionHeading.textContent.trim();
                const options = Array.from(question.querySelectorAll('.options li span')).map(span => span.textContent);
                const correctOption = options.find(opt => opt.startsWith(correctAnswer + '.'));
                const selectedOption = selectedAnswer ? options.find(opt => opt.startsWith(selectedAnswer + '.')) : 'Not answered';
                
                retryReviewHtml += `
                    <div class="answer-item ${{isCorrect ? 'answer-correct' : 'answer-incorrect'}}">
                        <strong>Retry Question ${{i}} (Original Q${{originalNum}}):</strong> ${{questionText.split(' Question')[0]}}<br>
                        <strong>Your answer:</strong> ${{selectedOption}}<br>
                        <strong>Correct answer:</strong> ${{correctOption}}
                    </div>
                `;
            }}

            window.failedQuestions = remainingFailedQuestions;

            showRetryResultsPage({{
                retryCorrect,
                totalRetried: window.retryQuestions.length,
                remainingCount: remainingFailedQuestions.length,
                retryReviewHtml
            }});

            window.retryMode = false;
        }}

        function showRetryResultsPage({{ retryCorrect, totalRetried, remainingCount, retryReviewHtml }}) {{
            document.getElementById('results').style.display = 'none';
            document.getElementById('quiz-container').style.display = 'none';
            document.querySelector('.navigation').style.display = 'none';
            document.getElementById('question-squares').style.display = 'none';
            document.getElementById('retry-results').style.display = 'block';

            document.getElementById('retry-summary').textContent = `${{retryCorrect}}/${{totalRetried}} correct (Retry)`;
            document.getElementById('retry-message').textContent =
                remainingCount > 0
                    ? `You still have ${{remainingCount}} failed question(s) remaining.`
                    : 'Perfect! You fixed all previously failed questions.';
            document.getElementById('retry-review').innerHTML = retryReviewHtml;

            const retryRemainingBtn = document.getElementById('retry-remaining-btn');
            if (remainingCount > 0) {{
                retryRemainingBtn.disabled = false;
                retryRemainingBtn.style.display = 'inline-block';
                retryRemainingBtn.textContent = `Retry Remaining Failed Questions (${{remainingCount}})`;
            }} else {{
                retryRemainingBtn.disabled = true;
                retryRemainingBtn.style.display = 'inline-block';
                retryRemainingBtn.textContent = 'Retry Remaining Failed Questions (0)';
            }}
        }}

        function backToOriginalResults() {{
            document.getElementById('retry-results').style.display = 'none';
            document.getElementById('results').style.display = 'block';
            document.getElementById('quiz-container').style.display = 'none';
            document.querySelector('.navigation').style.display = 'none';
            document.getElementById('question-squares').style.display = 'none';
        }}
        
        function validateQuiz() {{
            const unansweredQuestions = [];
            
            for (let i = 1; i <= totalQuestions; i++) {{
                const question = document.querySelector(`[data-question="${{i}}"]`);
                const questionType = question.dataset.type;
                
                let isAnswered = false;
                
                if (questionType === 'ordering') {{
                    // Check if ordering question has been confirmed
                    const container = document.getElementById(`ordering-${{i}}`);
                    isAnswered = container && container.classList.contains('completed');
                }} else {{
                    // Check MCQ questions
                    const selectedInput = document.querySelector(`input[name="q${{i}}"]:checked`);
                    isAnswered = !!selectedInput;
                }}
                
                if (!isAnswered) {{
                    unansweredQuestions.push(i);
                }}
            }}
            
            if (unansweredQuestions.length > 0) {{
                const warning = document.getElementById('unanswered-warning');
                const unansweredText = document.getElementById('unanswered-questions');
                
                warning.style.display = 'block';
                unansweredText.textContent = `Unanswered questions: ${{unansweredQuestions.join(', ')}}`;
                
                // Scroll to first unanswered question
                if (unansweredQuestions.length > 0) {{
                    showQuestion(unansweredQuestions[0]);
                }}
                
                return false;
            }}
            
            document.getElementById('unanswered-warning').style.display = 'none';
            return true;
        }}
        
        function submitQuiz() {{
            if (!validateQuiz()) {{
                return;
            }}
            
            let correct = 0;
            let reviewHtml = '';
            const failedQuestions = [];
            
            for (let i = 1; i <= totalQuestions; i++) {{
                const question = document.querySelector(`[data-question="${{i}}"]`);
                const correctAnswer = question.dataset.answer;
                const questionType = question.dataset.type;
                
                let selectedAnswer = '';
                let isCorrect = false;
                
                if (questionType === 'ordering') {{
                    // Handle ordering questions
                    selectedAnswer = getOrderingAnswer(i);
                    isCorrect = selectedAnswer === correctAnswer;
                }} else {{
                    // Handle MCQ questions
                    const selectedInput = question.querySelector(`input[name="q${{i}}"]:checked`);
                    selectedAnswer = selectedInput ? selectedInput.value : '';
                    isCorrect = selectedAnswer === correctAnswer;
                }}
                
                if (isCorrect) {{
                    correct++;
                }} else {{
                    failedQuestions.push(i);
                }}
                
                // Add to review
                const questionText = question.querySelector('h3').textContent.trim();
                
                let reviewContent = '';
                if (questionType === 'ordering') {{
                    // For ordering questions, show the user's order vs correct order
                    const container = document.getElementById(`ordering-${{i}}`);
                    const items = container.querySelectorAll('.ordering-item');
                    const userOrder = Array.from(items).map(item => item.querySelector('.order-text').textContent.trim());
                    
                    // Get correct order from question data
                    const correctOrderData = JSON.parse(question.dataset.options);
                    const correctOrder = correctAnswer.split('').map(letter => {{
                        const index = letter.charCodeAt(0) - 65; // A=0, B=1, etc.
                        return correctOrderData[index] || '';
                    }});
                    
                    reviewContent = `
                        <strong>Your order:</strong> ${{userOrder.join(' → ')}}<br>
                        <strong>Correct order:</strong> ${{correctOrder.join(' → ')}}
                    `;
                }} else {{
                    // For MCQ questions
                    const options = Array.from(question.querySelectorAll('.options li span')).map(span => span.textContent);
                    const correctOption = options.find(opt => opt.startsWith(correctAnswer + '.'));
                    const selectedOption = selectedAnswer ? options.find(opt => opt.startsWith(selectedAnswer + '.')) : 'Not answered';
                    
                    reviewContent = `
                        <strong>Your answer:</strong> ${{selectedOption}}<br>
                        <strong>Correct answer:</strong> ${{correctOption}}
                    `;
                }}
                
                reviewHtml += `
                    <div class="answer-item ${{isCorrect ? 'answer-correct' : 'answer-incorrect'}}">
                        <strong>Question ${{i}}:</strong> ${{questionText.split(' Question')[0]}}<br>
                        ${{reviewContent}}
                    </div>
                `;
            }}
            
            // Store failed questions for retry functionality
            window.failedQuestions = failedQuestions;
            
            // Show/hide retry button based on whether there are failed questions
            const retryBtn = document.getElementById('retry-failed-btn');
            if (failedQuestions.length > 0) {{
                retryBtn.style.display = 'inline-block';
                retryBtn.textContent = `Retry Failed Questions (${{failedQuestions.length}})`;
            }} else {{
                retryBtn.style.display = 'none';
            }}
            
            // Calculate score percentage
            const percentage = Math.round((correct / totalQuestions) * 100);
            
            // Determine score class and message
            let scoreClass, message;
            if (percentage >= 90) {{
                scoreClass = 'score-excellent';
                message = 'Outstanding! You\\'re a Git master! 🏆';
            }} else if (percentage >= 70) {{
                scoreClass = 'score-good';
                message = 'Great job! You have solid Git knowledge! 🌟';
            }} else if (percentage >= 50) {{
                scoreClass = 'score-average';
                message = 'Good effort! Keep practicing to improve! 📚';
            }} else {{
                scoreClass = 'score-poor';
                message = 'Keep learning! Git takes time to master! 💪';
            }}
            
            // Show results
            document.getElementById('quiz-container').style.display = 'none';
            document.querySelector('.navigation').style.display = 'none';
            document.getElementById('question-squares').style.display = 'none';
            document.getElementById('results').style.display = 'block';
            
            document.getElementById('score').className = `score ${{scoreClass}}`;
            document.getElementById('score').textContent = `${{correct}}/${{totalQuestions}} (${{percentage}}%)`;
            document.getElementById('score-message').textContent = message;
            document.getElementById('answer-review').innerHTML = reviewHtml;
        }}
        
        function retryFailedQuestions() {{
            // Reset quiz to show only failed questions
            if (!window.failedQuestions || window.failedQuestions.length === 0) {{
                alert('No failed questions to retry!');
                return;
            }}
            
            // Hide results and show quiz container
            document.getElementById('retry-results').style.display = 'none';
            document.getElementById('results').style.display = 'none';
            document.getElementById('quiz-container').style.display = 'block';
            document.querySelector('.navigation').style.display = 'flex';
            document.getElementById('question-squares').style.display = 'flex';
            
            // Clear all radio button selections
            document.querySelectorAll('input[type="radio"]').forEach(radio => {{
                radio.checked = false;
            }});
            
            // Hide all questions first and reset their display
            document.querySelectorAll('.question').forEach(question => {{
                question.style.display = 'none';
                question.classList.remove('active');
            }});
            
            // Set up retry mode
            window.retryMode = true;
            window.retryQuestions = [...window.failedQuestions];
            currentRetryQuestion = 1; // Initialize current retry question
            
            // Show failed questions and update their numbering, but keep them hidden initially
            window.failedQuestions.forEach((originalNum, retryIndex) => {{
                const question = document.querySelector(`[data-question="${{originalNum}}"]`);
                if (question) {{
                    // Update question number in the text
                    const questionHeading = question.querySelector('h3');
                    const originalText = questionHeading.textContent;
                    const updatedText = originalText.replace(/^\\d+\\./, `${{retryIndex + 1}}.`);
                    questionHeading.textContent = updatedText;
                    
                    // Update radio button names to use retry numbers
                    const radios = question.querySelectorAll('input[type="radio"]');
                    radios.forEach(radio => {{
                        radio.name = `q${{retryIndex + 1}}`;
                    }});
                    
                    // Keep the question hidden for now
                    question.style.display = 'none';
                }}
            }});
            
            // Initialize retry question squares
            initializeRetryQuestionSquares();
            
            // Show only the first failed question
            showRetryQuestion(1);
        }}
        
        function initializeRetryQuestionSquares() {{
            const squaresContainer = document.getElementById('question-squares');
            squaresContainer.innerHTML = '';
            
            for (let i = 1; i <= window.retryQuestions.length; i++) {{
                const square = document.createElement('div');
                square.className = 'question-square unanswered';
                square.textContent = i;
                square.onclick = () => showRetryQuestion(i);
                square.id = `retry-square-${{i}}`;
                squaresContainer.appendChild(square);
            }}
            
            updateRetrySquareStates();
        }}
        
        function updateRetrySquareStates() {{
            if (!window.retryMode) return;
            
            for (let i = 1; i <= window.retryQuestions.length; i++) {{
                const square = document.getElementById(`retry-square-${{i}}`);
                const selectedInput = document.querySelector(`input[name="q${{i}}"]:checked`);
                
                square.classList.remove('active', 'completed', 'unanswered');
                
                if (i === currentRetryQuestion) {{
                    square.classList.add('active');
                }} else if (selectedInput) {{
                    square.classList.add('completed');
                }} else {{
                    square.classList.add('unanswered');
                }}
            }}
        }}
        
        function showRetryQuestion(retryNum) {{
            // Hide all retry questions first
            window.failedQuestions.forEach(originalNum => {{
                const question = document.querySelector(`[data-question="${{originalNum}}"]`);
                if (question) {{
                    question.style.display = 'none';
                    question.classList.remove('active');
                }}
            }});
            
            // Show only the current retry question
            const originalNum = window.retryQuestions[retryNum - 1];
            const questionToShow = document.querySelector(`[data-question="${{originalNum}}"]`);
            if (questionToShow) {{
                questionToShow.style.display = 'block';
                questionToShow.classList.add('active');
            }}
            
            // Update navigation
            currentRetryQuestion = retryNum;
            updateRetryProgress();
            updateRetrySquareStates();
        }}
        
        function updateRetryProgress() {{
            if (!window.retryMode) return;
            
            const progress = (currentRetryQuestion / window.retryQuestions.length) * 100;
            document.getElementById('progress').style.width = `${{progress}}%`;
            document.getElementById('question-counter').textContent = 
                `Failed Question ${{currentRetryQuestion}} of ${{window.retryQuestions.length}}`;
            
            // Update navigation buttons
            document.getElementById('prev-btn').disabled = currentRetryQuestion === 1;
            document.getElementById('next-btn').textContent = 
                currentRetryQuestion === window.retryQuestions.length ? 'Submit Retry' : 'Next';
            document.getElementById('next-btn').className = 
                currentRetryQuestion === window.retryQuestions.length ? 'btn btn-danger' : 'btn';
        }}
        
        function generateNewQuestions() {{
            // Ask the local quiz server to generate a fresh quiz that excludes previously used questions
            window.location.href = '/generate';
        }}
        
        function generateNewQuiz() {{
            // Legacy function - redirect to new function
            generateNewQuestions();
        }}
        
        // Add keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowRight' && currentQuestion < totalQuestions) {{
                nextQuestion();
            }} else if (e.key === 'ArrowLeft' && currentQuestion > 1) {{
                previousQuestion();
            }} else if (e.key === 'Enter') {{
                submitQuiz();
            }}
        }});
        
        // Add event listeners for radio buttons to update squares in real-time
        document.addEventListener('change', function(e) {{
            if (e.target.type === 'radio') {{
                updateSquareStates();
            }}
        }});
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            initializeQuestionSquares();
            initializeOrderingQuestions();
            showQuestion(1);
        }});
    </script>
</body>
</html>"""
        
        return html
