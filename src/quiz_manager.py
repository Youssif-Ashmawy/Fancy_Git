#!/usr/bin/env python3
import os
import json
import random
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    from src.colors import color_success, color_info, color_error, color_warning
    from src.quiz_html_generator import QuizHTMLGenerator
except ImportError:
    from colors import color_success, color_info, color_error, color_warning
    from quiz_html_generator import QuizHTMLGenerator


class QuizManager:
    def __init__(self):
        self._quiz_httpd = None
        self._quiz_server_thread = None
        self._quiz_server_port = None
        self.html_generator = QuizHTMLGenerator()
    
    def launch_quiz(self):
        """Launch a web-based Git quiz using questions from game_questions.json"""
        try:
            # Load questions from JSON file
            script_dir = os.path.dirname(os.path.realpath(__file__))
            # Go up one level since we're in src/ directory
            script_dir = os.path.dirname(script_dir)
            
            questions_file = os.path.join(script_dir, 'game_questions.json')
            used_questions_file = os.path.join(script_dir, '.used_questions.json')
            
            if not os.path.exists(questions_file):
                print(color_error("❌ game_questions.json file not found"))
                return False
            
            # Reset used questions file for fresh start
            try:
                with open(used_questions_file, 'w') as f:
                    json.dump([], f)
                print(color_info("🔄 Reset question pool - all questions are now available"))
            except Exception as e:
                print(color_warning(f"⚠️  Could not reset used questions file: {e}"))

            with open(questions_file, 'r') as f:
                all_questions = json.load(f)

            used_ids = []  # Start with empty used questions list
            unused_questions = all_questions[:]  # All questions are available

            quiz_questions = random.sample(unused_questions, min(15, len(unused_questions)))
            random.shuffle(quiz_questions)

            selected_ids = [q.get('id') for q in quiz_questions if q.get('id') is not None]
            try:
                next_used = list(dict.fromkeys((used_ids or []) + selected_ids))
                with open(used_questions_file, 'w') as f:
                    json.dump(next_used, f, indent=2)
            except Exception:
                pass
            
            # Create HTML content
            html_content = self.html_generator.generate_quiz_html(quiz_questions)
            
            # Write HTML file
            quiz_file = os.path.join(script_dir, 'quiz.html')
            with open(quiz_file, 'w') as f:
                f.write(html_content)
            
            self._start_quiz_server(script_dir)

            print(color_success("🎯 Git Quiz Started!"))
            print(color_info(f"📝 {len(quiz_questions)} fresh questions"))
            print(color_info("🌐 Opening quiz in your browser..."))

            webbrowser.open(f'http://127.0.0.1:{self._quiz_server_port}/quiz')
            
            return True
            
        except Exception as e:
            print(color_error(f"❌ Failed to launch quiz: {e}"))
            return False

    def _start_quiz_server(self, script_dir):
        if self._quiz_httpd is not None:
            return

        quiz_manager_instance = self

        class QuizHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=script_dir, **kwargs)

            def do_GET(self):
                if self.path in ('/', '/quiz'):
                    self.path = '/quiz.html'
                    return super().do_GET()

                if self.path == '/generate':
                    try:
                        result = quiz_manager_instance._regenerate_quiz(script_dir)
                        if result:
                            # Return JSON response with new questions and status
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(result).encode())
                        else:
                            self.send_response(500)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({'error': 'Failed to generate questions'}).encode())
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': str(e)}).encode())
                    return

                if self.path == '/api/questions':
                    try:
                        result = quiz_manager_instance._get_question_status(script_dir)
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': str(e)}).encode())
                    return

                return super().do_GET()

            def log_message(self, format, *args):
                return

        self._quiz_httpd = HTTPServer(('127.0.0.1', 0), QuizHandler)
        self._quiz_server_port = self._quiz_httpd.server_address[1]
        self._quiz_server_thread = threading.Thread(target=self._quiz_httpd.serve_forever, daemon=True)
        self._quiz_server_thread.start()

    def _regenerate_quiz(self, script_dir):
        """Generate new quiz questions and return JSON response"""
        questions_file = os.path.join(script_dir, 'game_questions.json')
        used_questions_file = os.path.join(script_dir, '.used_questions.json')

        with open(questions_file, 'r') as f:
            all_questions = json.load(f)

        used_ids = []
        try:
            if os.path.exists(used_questions_file):
                with open(used_questions_file, 'r') as f:
                    used_ids = json.load(f) or []
        except Exception:
            used_ids = []

        unused_questions = [q for q in all_questions if q.get('id') not in set(used_ids)]
        total_questions = len(all_questions)
        used_count = len(used_ids)
        unused_count = len(unused_questions)
        
        # Check if we have enough unused questions
        questions_needed = 15
        pool_exhausted = False
        
        if len(unused_questions) < questions_needed:
            pool_exhausted = True
            # Reset the used questions pool
            used_ids = []
            unused_questions = all_questions[:]

        quiz_questions = random.sample(unused_questions, questions_needed)
        random.shuffle(quiz_questions)

        selected_ids = [q.get('id') for q in quiz_questions if q.get('id') is not None]
        try:
            next_used = list(dict.fromkeys((used_ids or []) + selected_ids))
            with open(used_questions_file, 'w') as f:
                json.dump(next_used, f, indent=2)
        except Exception:
            pass

        # Generate HTML content
        html_content = self.html_generator.generate_quiz_html(quiz_questions)
        quiz_file = os.path.join(script_dir, 'quiz.html')
        with open(quiz_file, 'w') as f:
            f.write(html_content)

        return {
            'success': True,
            'questions': quiz_questions,
            'pool_exhausted': pool_exhausted,
            'total_questions': total_questions,
            'used_count': used_count,
            'unused_count': unused_count,
            'message': 'Question pool has been reset - all questions are now available!' if pool_exhausted else 'New questions generated successfully!'
        }

    def _get_question_status(self, script_dir):
        """Get current question pool status"""
        questions_file = os.path.join(script_dir, 'game_questions.json')
        used_questions_file = os.path.join(script_dir, '.used_questions.json')

        with open(questions_file, 'r') as f:
            all_questions = json.load(f)

        used_ids = []
        try:
            if os.path.exists(used_questions_file):
                with open(used_questions_file, 'r') as f:
                    used_ids = json.load(f) or []
        except Exception:
            used_ids = []

        unused_questions = [q for q in all_questions if q.get('id') not in set(used_ids)]
        
        return {
            'total_questions': len(all_questions),
            'used_count': len(used_ids),
            'unused_count': len(unused_questions),
            'can_generate': len(unused_questions) >= 15
        }
