"""
SQLite Database Management Module for Musicbot
Handles all database operations including connection management, 
table creation, and CRUD operations.
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite Database Manager for Musicbot
    Provides connection pooling, transaction management, and common operations
    """

    def __init__(self, db_path: str = "musicbot.db"):
        """
        Initialize the database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self._ensure_database_exists()
        self._initialize_tables()

    def _ensure_database_exists(self) -> None:
        """Create database file if it doesn't exist"""
        db_dir = Path(self.db_path).parent
        if db_dir != Path(".") and not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Ensures proper connection handling and cleanup
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def _initialize_tables(self) -> None:
        """Create necessary database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Playlists table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    playlist_name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Songs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    duration INTEGER,
                    url TEXT UNIQUE,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Playlist Songs (junction table)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlist_songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER NOT NULL,
                    song_id INTEGER NOT NULL,
                    position INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
                    FOREIGN KEY (song_id) REFERENCES songs(id),
                    UNIQUE(playlist_id, song_id)
                )
            """)
            
            # User Preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    theme TEXT DEFAULT 'dark',
                    volume INTEGER DEFAULT 50,
                    language TEXT DEFAULT 'en',
                    auto_play BOOLEAN DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Playback History table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playback_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    song_id INTEGER NOT NULL,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_played INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (song_id) REFERENCES songs(id)
                )
            """)
            
            logger.info("Database tables initialized successfully")

    # User Operations
    def add_user(self, user_id: str, username: str) -> bool:
        """
        Add a new user to the database
        
        Args:
            user_id: Unique user identifier
            username: Display name for the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (user_id, username)
                    VALUES (?, ?)
                """, (user_id, username))
                logger.info(f"User {username} added successfully")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"User {user_id} already exists")
            return False

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information by user_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            return [dict(row) for row in cursor.fetchall()]

    # Song Operations
    def add_song(self, title: str, artist: str, duration: int, 
                 url: Optional[str] = None, file_path: Optional[str] = None) -> Optional[int]:
        """
        Add a new song to the database
        
        Args:
            title: Song title
            artist: Artist name
            duration: Song duration in seconds
            url: Optional URL to the song
            file_path: Optional local file path
            
        Returns:
            Song ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO songs (title, artist, duration, url, file_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, artist, duration, url, file_path))
                song_id = cursor.lastrowid
                logger.info(f"Song '{title}' by {artist} added with ID {song_id}")
                return song_id
        except sqlite3.IntegrityError:
            logger.warning(f"Song URL {url} already exists")
            return None

    def get_song(self, song_id: int) -> Optional[Dict[str, Any]]:
        """Get song information by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_songs(self, query: str) -> List[Dict[str, Any]]:
        """Search songs by title or artist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM songs 
                WHERE title LIKE ? OR artist LIKE ?
                ORDER BY title
            """, (f"%{query}%", f"%{query}%"))
            return [dict(row) for row in cursor.fetchall()]

    # Playlist Operations
    def create_playlist(self, user_id: str, playlist_name: str, 
                       description: Optional[str] = None) -> Optional[int]:
        """
        Create a new playlist for a user
        
        Args:
            user_id: User identifier
            playlist_name: Name of the playlist
            description: Optional description
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO playlists (user_id, playlist_name, description)
                    VALUES (?, ?, ?)
                """, (user_id, playlist_name, description))
                playlist_id = cursor.lastrowid
                logger.info(f"Playlist '{playlist_name}' created with ID {playlist_id}")
                return playlist_id
        except sqlite3.Error as e:
            logger.error(f"Error creating playlist: {e}")
            return None

    def get_user_playlists(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all playlists for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM playlists 
                WHERE user_id = ?
                ORDER BY updated_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_playlist(self, playlist_id: int) -> Optional[Dict[str, Any]]:
        """Get playlist information by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist and its songs"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Delete playlist songs first
                cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
                # Delete playlist
                cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
                logger.info(f"Playlist {playlist_id} deleted successfully")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting playlist: {e}")
            return False

    # Playlist Songs Operations
    def add_song_to_playlist(self, playlist_id: int, song_id: int, 
                            position: Optional[int] = None) -> bool:
        """
        Add a song to a playlist
        
        Args:
            playlist_id: ID of the playlist
            song_id: ID of the song
            position: Optional position in playlist (auto-increment if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if position is None:
                    # Get the next position
                    cursor.execute("""
                        SELECT MAX(position) FROM playlist_songs WHERE playlist_id = ?
                    """, (playlist_id,))
                    result = cursor.fetchone()
                    position = (result[0] or 0) + 1
                
                cursor.execute("""
                    INSERT INTO playlist_songs (playlist_id, song_id, position)
                    VALUES (?, ?, ?)
                """, (playlist_id, song_id, position))
                logger.info(f"Song {song_id} added to playlist {playlist_id}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Song {song_id} already in playlist {playlist_id}")
            return False

    def get_playlist_songs(self, playlist_id: int) -> List[Dict[str, Any]]:
        """Get all songs in a playlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, ps.position, ps.added_at
                FROM songs s
                JOIN playlist_songs ps ON s.id = ps.song_id
                WHERE ps.playlist_id = ?
                ORDER BY ps.position
            """, (playlist_id,))
            return [dict(row) for row in cursor.fetchall()]

    def remove_song_from_playlist(self, playlist_id: int, song_id: int) -> bool:
        """Remove a song from a playlist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM playlist_songs 
                    WHERE playlist_id = ? AND song_id = ?
                """, (playlist_id, song_id))
                logger.info(f"Song {song_id} removed from playlist {playlist_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error removing song: {e}")
            return False

    # User Preferences Operations
    def set_user_preference(self, user_id: str, **preferences) -> bool:
        """
        Set or update user preferences
        
        Args:
            user_id: User identifier
            **preferences: Preference key-value pairs
            
        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if preferences exist
                cursor.execute("SELECT id FROM user_preferences WHERE user_id = ?", (user_id,))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing preferences
                    set_clause = ", ".join([f"{k} = ?" for k in preferences.keys()])
                    values = list(preferences.values()) + [user_id]
                    cursor.execute(f"""
                        UPDATE user_preferences 
                        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, values)
                else:
                    # Insert new preferences
                    cols = ", ".join(["user_id"] + list(preferences.keys()))
                    placeholders = ", ".join(["?"] * (len(preferences) + 1))
                    values = [user_id] + list(preferences.values())
                    cursor.execute(f"""
                        INSERT INTO user_preferences ({cols})
                        VALUES ({placeholders})
                    """, values)
                
                logger.info(f"Preferences updated for user {user_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error updating preferences: {e}")
            return False

    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # Playback History Operations
    def log_playback(self, user_id: str, song_id: int, 
                    duration_played: Optional[int] = None) -> bool:
        """
        Log a song playback in history
        
        Args:
            user_id: User identifier
            song_id: Song ID that was played
            duration_played: Optional duration played in seconds
            
        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO playback_history (user_id, song_id, duration_played)
                    VALUES (?, ?, ?)
                """, (user_id, song_id, duration_played))
                logger.info(f"Playback logged for user {user_id}, song {song_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error logging playback: {e}")
            return False

    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get playback history for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ph.*, s.title, s.artist
                FROM playback_history ph
                JOIN songs s ON ph.song_id = s.id
                WHERE ph.user_id = ?
                ORDER BY ph.played_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # Database Maintenance
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for table in ['users', 'songs', 'playlists', 'playback_history']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
        
        return stats

    def clear_history(self, user_id: Optional[str] = None) -> bool:
        """
        Clear playback history
        
        Args:
            user_id: Optional user ID to clear only that user's history
            
        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute("DELETE FROM playback_history WHERE user_id = ?", (user_id,))
                    logger.info(f"History cleared for user {user_id}")
                else:
                    cursor.execute("DELETE FROM playback_history")
                    logger.info("All playback history cleared")
                
                return True
        except sqlite3.Error as e:
            logger.error(f"Error clearing history: {e}")
            return False

    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


# Initialize database manager
db_manager = DatabaseManager()


if __name__ == "__main__":
    # Example usage
    print("Musicbot Database Manager initialized successfully")
    stats = db_manager.get_database_stats()
    print(f"Database Statistics: {stats}")
