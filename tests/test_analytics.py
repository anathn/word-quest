"""
Tests for Analytics Component

Tests for STORY-002-06: Progress Graph (Fluency Trend)
"""

import pytest
from datetime import datetime, timedelta
from src.components.analytics import AnalyticsEngine, DataPoint, create_analytics_engine


class TestAnalyticsEngine:
    """Test the AnalyticsEngine class."""
    
    def create_sample_sessions(self, days_ago=7, num_words=3, attempts_per_word=2):
        """Helper to create sample session data."""
        sessions = []
        base_date = datetime.now()
        
        for i in range(days_ago):
            session_date = base_date - timedelta(days=i)
            session = {
                'session_id': f'session_{i}',
                'student_id': 'test_student',
                'start_time': session_date.isoformat(),
                'words': []
            }
            
            for j in range(num_words):
                session['words'].append({
                    'word': f'word_{j}',
                    'word_id': f'word_id_{j}',
                    'correct': True,
                    'first_attempt_correct': attempts_per_word == 1,
                    'total_attempts': attempts_per_word,
                    'hints_used': 0,
                    'time_seconds': 10.0,
                    'timestamp': session_date.isoformat()
                })
            
            sessions.append(session)
        
        return sessions
    
    def test_initialization(self):
        """Test AnalyticsEngine initialization."""
        sessions = [{'session_id': 'test'}]
        engine = AnalyticsEngine(sessions=sessions)
        
        assert engine.sessions == sessions
        assert engine._weekly_cache is None
    
    def test_factory_function(self):
        """Test create_analytics_engine factory function."""
        sessions = [{'session_id': 'test'}]
        engine = create_analytics_engine(sessions=sessions)
        
        assert isinstance(engine, AnalyticsEngine)
        assert engine.sessions == sessions
    
    def test_get_weekly_averages_basic(self):
        """Test basic weekly average calculation."""
        # Create 3 days of data with 2 attempts per word
        sessions = self.create_sample_sessions(days_ago=3, num_words=2, attempts_per_word=2)
        engine = AnalyticsEngine(sessions=sessions)
        
        data = engine.get_weekly_averages(weeks=8)
        
        # Should return 8 weeks
        assert len(data) == 8
        
        # Weeks with data should have average of 2.0
        weeks_with_data = [d for d in data if d.word_count > 0]
        for week in weeks_with_data:
            assert week.average == 2.0
            assert week.word_count > 0
    
    def test_get_weekly_averages_empty(self):
        """Test weekly averages with no data."""
        engine = AnalyticsEngine(sessions=[])
        
        data = engine.get_weekly_averages(weeks=8)
        
        assert len(data) == 8
        for point in data:
            assert point.average == 0
            assert point.word_count == 0
    
    def test_get_weekly_averages_mixed_data(self):
        """Test with some weeks having data and some empty."""
        sessions = self.create_sample_sessions(days_ago=5, num_words=2, attempts_per_word=2)
        engine = AnalyticsEngine(sessions=sessions)
        
        data = engine.get_weekly_averages(weeks=2)
        
        # Should have 2 weeks
        assert len(data) == 2
        
        # Fill in missing weeks should ensure continuity
        for point in data:
            assert point.week is not None
            assert isinstance(point.average, float)
    
    def test_get_weekly_averages_various_attempts(self):
        """Test with varying attempt counts."""
        sessions = [
            {
                'session_id': 's1',
                'student_id': 'test',
                'start_time': datetime.now().isoformat(),
                'words': [
                    {'word': 'w1', 'word_id': '1', 'total_attempts': 1},
                    {'word': 'w2', 'word_id': '2', 'total_attempts': 2},
                    {'word': 'w3', 'word_id': '3', 'total_attempts': 3}
                ]
            }
        ]
        
        engine = AnalyticsEngine(sessions=sessions)
        data = engine.get_weekly_averages(weeks=1)
        
        # Average of 1, 2, 3 = 2.0
        assert len(data) == 1
        assert data[0].average == 2.0
        assert data[0].word_count == 3
    
    def test_get_trend_direction_insufficient_data(self):
        """Test trend direction with insufficient data."""
        engine = AnalyticsEngine(sessions=[])
        
        trend = engine.get_trend_direction([])
        assert trend == "insufficient"
        
        # Only one week of data
        one_week = [DataPoint(week="2026-W27", average=2.0, word_count=5)]
        trend = engine.get_trend_direction(one_week)
        assert trend == "insufficient"
    
    def test_get_trend_direction_improving(self):
        """Test detecting improving trend (decreasing attempts)."""
        engine = AnalyticsEngine(sessions=[])
        
        # First week has higher attempts, last week has lower
        data = [
            DataPoint(week="2026-W20", average=3.0, word_count=5),
            DataPoint(week="2026-W21", average=2.5, word_count=5),
            DataPoint(week="2026-W22", average=1.5, word_count=5),
            DataPoint(week="2026-W23", average=1.2, word_count=5),
        ]
        
        trend = engine.get_trend_direction(data)
        assert trend == "improving"
    
    def test_get_trend_direction_declining(self):
        """Test detecting declining trend (increasing attempts)."""
        engine = AnalyticsEngine(sessions=[])
        
        data = [
            DataPoint(week="2026-W20", average=1.5, word_count=5),
            DataPoint(week="2026-W21", average=1.8, word_count=5),
            DataPoint(week="2026-W22", average=2.5, word_count=5),
            DataPoint(week="2026-W23", average=3.0, word_count=5),
        ]
        
        trend = engine.get_trend_direction(data)
        assert trend == "declining"
    
    def test_get_trend_direction_stable(self):
        """Test detecting stable trend."""
        engine = AnalyticsEngine(sessions=[])
        
        data = [
            DataPoint(week="2026-W20", average=2.0, word_count=5),
            DataPoint(week="2026-W21", average=2.1, word_count=5),
            DataPoint(week="2026-W22", average=1.9, word_count=5),
            DataPoint(week="2026-W23", average=2.0, word_count=5),
        ]
        
        trend = engine.get_trend_direction(data)
        assert trend == "stable"
    
    def test_get_trend_direction_zero_data(self):
        """Test trend with weeks having zero data."""
        engine = AnalyticsEngine(sessions=[])
        
        # All data has word_count=0, so there's no actual data to determine trend
        data = [
            DataPoint(week="2026-W20", average=0, word_count=0),
            DataPoint(week="2026-W21", average=0, word_count=0),
            DataPoint(week="2026-W22", average=0, word_count=0),
        ]
        
        # Should return insufficient since there's no actual data
        trend = engine.get_trend_direction(data)
        assert trend == "insufficient"
    
    def test_get_insufficient_data_message(self):
        """Test the insufficient data message."""
        engine = AnalyticsEngine(sessions=[])
        
        message = engine.get_insufficient_data_message()
        assert "data" in message.lower()
        assert "session" in message.lower()
    
    def test_calculate_fluency_score_empty(self):
        """Test fluency score with no data."""
        engine = AnalyticsEngine(sessions=[])
        
        score = engine.calculate_fluency_score([])
        assert score == 0.0
    
    def test_calculate_fluency_score_basic(self):
        """Test basic fluency score calculation."""
        engine = AnalyticsEngine(sessions=[])
        
        data = [
            DataPoint(week="2026-W20", average=3.0, word_count=5),
            DataPoint(week="2026-W21", average=2.0, word_count=5),
            DataPoint(week="2026-W22", average=1.0, word_count=5),
        ]
        
        score = engine.calculate_fluency_score(data)
        
        # Weighted average: (3*1 + 2*2 + 1*3) / (1+2+3) = (3+4+3)/6 = 10/6 = 1.67
        assert 1.6 <= score <= 1.7
    
    def test_data_point_immutability(self):
        """Test that DataPoint is immutable (namedtuple)."""
        point = DataPoint(week="2026-W27", average=2.0, word_count=5)
        
        assert point.week == "2026-W27"
        assert point.average == 2.0
        assert point.word_count == 5
        
        # Try to modify (should raise error since namedtuple)
        with pytest.raises(AttributeError):
            point.average = 3.0
    
    def test_week_key_format(self):
        """Test that week keys follow ISO format."""
        sessions = self.create_sample_sessions(days_ago=7, num_words=1, attempts_per_word=2)
        engine = AnalyticsEngine(sessions=sessions)
        
        data = engine.get_weekly_averages(weeks=2)
        
        for point in data:
            # Week key should contain "-W" for ISO week format
            if point.word_count > 0:
                assert "-W" in point.week or point.week[4] == 'W'


class TestAnalyticsEdgeCases:
    """Test edge cases and error handling."""
    
    def test_all_zero_attempts(self):
        """Test with all words having 0 attempts (edge case)."""
        sessions = [
            {
                'session_id': 's1',
                'student_id': 'test',
                'start_time': datetime.now().isoformat(),
                'words': [
                    {'word': 'w1', 'word_id': '1', 'total_attempts': 0},
                    {'word': 'w2', 'word_id': '2', 'total_attempts': 0}
                ]
            }
        ]
        
        engine = AnalyticsEngine(sessions=sessions)
        data = engine.get_weekly_averages(weeks=1)
        
        # Should handle zero attempts gracefully
        assert len(data) == 1
        # Average of 0, 0 = 0
        assert data[0].average == 0.0
    
    def test_single_session(self):
        """Test with only one session."""
        sessions = [
            {
                'session_id': 's1',
                'student_id': 'test',
                'start_time': datetime.now().isoformat(),
                'words': [{'word': 'w1', 'word_id': '1', 'total_attempts': 2}]
            }
        ]
        
        engine = AnalyticsEngine(sessions=sessions)
        data = engine.get_weekly_averages(weeks=8)
        
        # Should fill in rest with zeros
        assert len(data) == 8
        non_zero_weeks = [d for d in data if d.word_count > 0]
        assert len(non_zero_weeks) == 1
    
    def test_large_dataset(self):
        """Test with a larger dataset."""
        sessions = []
        for i in range(30):  # 30 sessions
            session = {
                'session_id': f'session_{i}',
                'student_id': 'test',
                'start_time': (datetime.now() - timedelta(days=i)).isoformat(),
                'words': [
                    {'word': f'w{j}', 'word_id': f'id_{j}', 'total_attempts': (j % 3) + 1}
                    for j in range(10)
                ]
            }
            sessions.append(session)
        
        engine = AnalyticsEngine(sessions=sessions)
        data = engine.get_weekly_averages(weeks=8)
        
        assert len(data) == 8
        for point in data:
            assert point.word_count >= 0
            assert point.average >= 0
    
    def test_invalid_session_data(self):
        """Test handling of malformed session data."""
        sessions = [
            {'session_id': 's1'},  # Missing words
            {
                'session_id': 's2',
                'student_id': 'test',
                'start_time': datetime.now().isoformat(),
                'words': [{}]  # Empty word data
            }
        ]
        
        engine = AnalyticsEngine(sessions=sessions)
        data = engine.get_weekly_averages(weeks=2)
        
        # Should handle gracefully
        assert len(data) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])