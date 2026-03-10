import subprocess
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any

class GitInsights:
    def __init__(self, git_runner):
        self.runner = git_runner
    
    def get_commit_frequency(self, days: int = 30) -> Dict[str, int]:
        """Get commit frequency per contributor over specified days"""
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        returncode, stdout, stderr = self.runner.run_git_command([
            'log', '--since', since_date, '--pretty=format:%an', '--date=short'
        ])
        
        if returncode != 0:
            return {}
        
        authors = stdout.strip().split('\n') if stdout.strip() else []
        return dict(Counter(authors))
    
    def get_lines_changed_over_time(self, days: int = 30) -> List[Dict]:
        """Get lines added/removed over time"""
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        returncode, stdout, stderr = self.runner.run_git_command([
            'log', '--since', since_date, '--pretty=format:%H|%ad|%an', 
            '--date=short', '--numstat'
        ])
        
        if returncode != 0:
            return []
        
        commits = []
        current_commit = {}
        
        for line in stdout.strip().split('\n'):
            if '|' in line and len(line.split('|')) == 3:
                if current_commit:
                    commits.append(current_commit)
                hash_val, date, author = line.split('|')
                current_commit = {
                    'hash': hash_val,
                    'date': date,
                    'author': author,
                    'files_changed': 0,
                    'lines_added': 0,
                    'lines_removed': 0
                }
            elif line.strip() and '\t' in line and current_commit:
                # Parse numstat line: "10    5    file.py"
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    try:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        removed = int(parts[1]) if parts[1] != '-' else 0
                        current_commit['lines_added'] += added
                        current_commit['lines_removed'] += removed
                        current_commit['files_changed'] += 1
                    except ValueError:
                        # Skip binary files
                        continue
        
        if current_commit:
            commits.append(current_commit)
        
        return commits
    
    def get_branch_analysis(self) -> Dict[str, Any]:
        """Analyze branches - active vs stale, separating local and remote"""
        branch_info = {}
        now = datetime.now()
        
        # First, fetch latest remote data to ensure we have up-to-date branch information
        self.runner.run_git_command(['fetch', '--all'])
        
        # Get local branches
        returncode, stdout, stderr = self.runner.run_git_command(['branch'])
        if returncode == 0:
            for line in stdout.strip().split('\n'):
                if line.strip():
                    branch = line.strip().replace('* ', '')
                    branch_name = f"local/{branch}"
                    
                    # Get last commit date for branch
                    commit_returncode, commit_stdout, _ = self.runner.run_git_command([
                        'log', '-1', '--pretty=format:%ad', '--date=iso', branch
                    ])
                    
                    if commit_returncode == 0 and commit_stdout.strip():
                        try:
                            # Parse ISO date with timezone info
                            date_str = commit_stdout.strip()
                            if ' ' in date_str:
                                # Format like "2026-03-10 02:46:15 +0300"
                                last_commit_date = datetime.strptime(date_str.split()[0] + ' ' + date_str.split()[1], "%Y-%m-%d %H:%M:%S")
                            else:
                                # Format like "2026-03-10"
                                last_commit_date = datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            # Fallback to simple date parsing
                            last_commit_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                        
                        days_inactive = (now - last_commit_date).days
                        
                        branch_info[branch_name] = {
                            'last_commit': commit_stdout.strip(),
                            'days_inactive': days_inactive,
                            'status': 'active' if days_inactive <= 30 else 'stale',
                            'type': 'local'
                        }
        
        # Get remote branches
        returncode, stdout, stderr = self.runner.run_git_command(['branch', '-r'])
        if returncode == 0:
            for line in stdout.strip().split('\n'):
                if line.strip():
                    branch = line.strip().replace('* ', '').replace('remotes/', '')
                    if not branch.startswith('HEAD ->'):
                        branch_name = f"remote/{branch}"
                        
                        # Get last commit date for branch
                        commit_returncode, commit_stdout, _ = self.runner.run_git_command([
                            'log', '-1', '--pretty=format:%ad', '--date=iso', branch
                        ])
                        
                        if commit_returncode == 0 and commit_stdout.strip():
                            try:
                                # Parse ISO date with timezone info
                                date_str = commit_stdout.strip()
                                if ' ' in date_str:
                                    # Format like "2026-03-10 02:46:15 +0300"
                                    last_commit_date = datetime.strptime(date_str.split()[0] + ' ' + date_str.split()[1], "%Y-%m-%d %H:%M:%S")
                                else:
                                    # Format like "2026-03-10"
                                    last_commit_date = datetime.strptime(date_str, "%Y-%m-%d")
                            except ValueError:
                                # Fallback to simple date parsing
                                last_commit_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                            
                            days_inactive = (now - last_commit_date).days
                            
                            branch_info[branch_name] = {
                                'last_commit': commit_stdout.strip(),
                                'days_inactive': days_inactive,
                                'status': 'active' if days_inactive <= 30 else 'stale',
                                'type': 'remote'
                            }
        
        return branch_info
    
    def get_file_hotspots(self, days: int = 90) -> Dict[str, int]:
        """Get files/directories with most changes"""
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        returncode, stdout, stderr = self.runner.run_git_command([
            'log', '--since', since_date, '--name-only', '--pretty=format:'
        ])
        
        if returncode != 0:
            return {}
        
        files = []
        for line in stdout.split('\n'):
            if line.strip():
                files.append(line.strip())
        
        return dict(Counter(files))
    
    def get_merge_efficiency(self, days: int = 90) -> Dict[str, Any]:
        """Analyze merge/pull request efficiency"""
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get merge commits
        returncode, stdout, stderr = self.runner.run_git_command([
            'log', '--since', since_date, '--merges', '--pretty=format:%H|%ad|%s', 
            '--date=iso'
        ])
        
        if returncode != 0:
            return {}
        
        merges = []
        for line in stdout.strip().split('\n'):
            if '|' in line:
                hash_val, date, subject = line.split('|', 2)
                merges.append({
                    'hash': hash_val,
                    'date': date,
                    'subject': subject
                })
        
        # Calculate average time between merge commits
        if len(merges) < 2:
            return {'total_merges': len(merges), 'avg_merge_interval_days': 0}
        
        merge_dates = []
        for merge in merges:
            try:
                date_str = merge['date']
                if ' ' in date_str:
                    # Format like "2026-03-10 02:46:15 +0300"
                    merge_date = datetime.strptime(date_str.split()[0] + ' ' + date_str.split()[1], "%Y-%m-%d %H:%M:%S")
                else:
                    # Format like "2026-03-10"
                    merge_date = datetime.strptime(date_str, "%Y-%m-%d")
                merge_dates.append(merge_date)
            except ValueError:
                # Skip invalid dates
                continue
        
        if len(merge_dates) < 2:
            return {'total_merges': len(merges), 'avg_merge_interval_days': 0}
        
        merge_dates.sort()
        
        intervals = []
        for i in range(1, len(merge_dates)):
            interval = (merge_dates[i] - merge_dates[i-1]).days
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        return {
            'total_merges': len(merges),
            'avg_merge_interval_days': round(avg_interval, 1),
            'recent_merges': merges[-5:]  # Last 5 merges
        }
    
    def get_contributor_stats(self) -> Dict[str, Dict]:
        """Get comprehensive contributor statistics"""
        returncode, stdout, stderr = self.runner.run_git_command([
            'log', '--pretty=format:%an|%ad', '--date=iso', '--numstat'
        ])
        
        if returncode != 0:
            return {}
        
        contributors = defaultdict(lambda: {
            'commits': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'files_changed': 0,
            'first_commit': None,
            'last_commit': None
        })
        
        lines = stdout.strip().split('\n')
        current_author = None
        current_date = None
        
        for line in lines:
            if '|' in line and len(line.split('|')) == 2:
                author, date = line.split('|')
                current_author = author.strip()
                current_date = date.strip()
                
                if contributors[current_author]['first_commit'] is None:
                    contributors[current_author]['first_commit'] = current_date
                contributors[current_author]['last_commit'] = current_date
                contributors[current_author]['commits'] += 1
                
            elif line.strip() and '\t' in line and current_author:
                # Parse numstat line: "10    5    file.py"
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    try:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        removed = int(parts[1]) if parts[1] != '-' else 0
                        contributors[current_author]['lines_added'] += added
                        contributors[current_author]['lines_removed'] += removed
                        contributors[current_author]['files_changed'] += 1
                    except ValueError:
                        # Skip binary files or invalid numbers
                        continue
        
        return dict(contributors)
    
    def generate_insights_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive insights report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period_days': days,
            'commit_frequency': self.get_commit_frequency(days),
            'lines_changed': self.get_lines_changed_over_time(days),
            'branch_analysis': self.get_branch_analysis(),
            'file_hotspots': self.get_file_hotspots(days),
            'contributor_stats': self.get_contributor_stats()
        }
        
        # Add summary statistics
        total_commits = sum(report['commit_frequency'].values())
        active_branches = sum(1 for b in report['branch_analysis'].values() if b['status'] == 'active')
        
        report['summary'] = {
            'total_commits': total_commits,
            'active_contributors': len(report['commit_frequency']),
            'active_branches': active_branches,
            'total_branches': len(report['branch_analysis']),
            'total_files_changed': len(report['file_hotspots'])
        }
        
        return report
