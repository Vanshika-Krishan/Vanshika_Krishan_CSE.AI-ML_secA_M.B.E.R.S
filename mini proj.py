import streamlit as st
import random
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from PIL import Image
from io import BytesIO


# Constants for API keys (replace with your own)
SPOTIPY_CLIENT_ID = '51f9267bfa2b43a98a071a1fd7a39104'  # Replace with your actual Spotify Client ID
SPOTIPY_CLIENT_SECRET = '8f39b5a827e74f91a3451001a7c792e4'  # Replace with your actual Spotify Client Secret
WATCHMODE_API_KEY = "F0pX9Q68dyMLcvp7EY8F8O8tTlBKCIliEc6kS2t9"  # Replace with your actual Watchmode API key
# Base URL
BASE_URL = "https://api.watchmode.com/v1"

# Spotify API Setup with error handling
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))
except Exception as e:
    st.error(f"Failed to connect to Spotify API: {e}")
    sp = None

# Function to load and shuffle questions from a text file
def load_questions():
    questions = []
    try:
        with open(r'C:\Users\GOPAL\Desktop\pp\questions.txt', "r") as file:
            for line in file:
                question, category, weight = line.strip().split("|")
                questions.append((question, category, float(weight)))
        random.shuffle(questions)
    except FileNotFoundError:
        st.error("Questions file not found. Please ensure the file exists.")
    return questions

# Function to calculate MBTI type
def calculate_mbti(answers, questions):
    scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    for answer, (question, category, weight) in zip(answers, questions):  # Fixed variable name
        if category == "EI":
            scores["E"] += answer * weight
            scores["I"] += (8 - answer) * weight
        elif category == "SN":
            scores["S"] += answer * weight
            scores["N"] += (8 - answer) * weight
        elif category == "TF":
            scores["T"] += answer * weight
            scores["F"] += (8 - answer) * weight
        elif category == "JP":
            scores["J"] += answer * weight
            scores["P"] += (8 - answer) * weight
    mbti_type = "".join([
        "E" if scores["E"] > scores["I"] else "I",
        "S" if scores["S"] > scores["N"] else "N",
        "T" if scores["T"] > scores["F"] else "F",
        "J" if scores["J"] > scores["P"] else "P"
    ])
    return mbti_type

# Function to search for songs on Spotify
def search_spotify_songs(query):
    if sp is None:
        st.error("Spotify API is not initialized.")
        return []
    try:
        results = sp.search(q=query, limit=6, type='track')
        tracks = results['tracks']['items']
        track_details_list = []
        for track in tracks:
            track_details = {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album_name': track['album']['name'],
                'preview_url': track['preview_url'],
                'spotify_url': track['external_urls']['spotify'],
                'image_url': track['album']['images'][0]['url']
            }
            track_details_list.append(track_details)
        return track_details_list
    except Exception as e:
        st.error(f"Failed to fetch songs from Spotify: {e}")
        return []


# Function to fetch movies from Watchmode API
def search_watchmode_movies(genre_name, limit=5):
    """Fetch movies from Watchmode API based on a genre name."""
    genre_mapping = fetch_genre_ids()
    genre_id = genre_mapping.get(genre_name.lower())  # Get the genre ID for the given genre name

    if not genre_id:
        st.error(f"Genre '{genre_name}' not found in Watchmode API.")
        return []

    url = f"{BASE_URL}/list-titles/"
    params = {
        "apiKey": WATCHMODE_API_KEY.strip(),
        "genres": genre_id,
        "types": "movie",
        "limit": limit
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching movie data: {e}")
        return []

    if not data.get("titles"):
        st.error(f"No movies found for genre: {genre_name}")
        return []

    movies = []
    for item in data["titles"][:limit]:
        title = item.get("title", "Unknown Title")
        release_date = item.get("year", "Unknown Year")
        overview = item.get("plot_overview", "No plot available.")  # Fetch the movie plot
        poster_url = item.get("poster", None)
        # Use a default image if the poster URL is missing or invalid
        if not poster_url or not poster_url.startswith("http"):
            poster_url = "https://via.placeholder.com/200?text=Movie+Poster"  # Default image URL
        watchmode_url = f"https://www.watchmode.com/title/{item.get('id')}/"

        movies.append({
            'title': title,
            'release_date': release_date,
            'overview': overview,
            'image_url': poster_url,
            'watchmode_url': watchmode_url,
        })

    return movies

def filter_by_genre(movies, genre_name):
    """Filter movies by genre name"""
    filtered_movies = []
    
    for movie in movies:
        # Check if 'genres' key exists and if the genre is in the list
        if 'genre_names' in movie and genre_name in movie['genre_names']:
            filtered_movies.append(movie)
    
    return filtered_movies

def get_movie_details(movie_id):
    """Get detailed information about a movie"""
    url = f"{BASE_URL}/title/{movie_id}/details/"
    params = {"apiKey": WATCHMODE_API_KEY}
    response = requests.get(url, params=params)
    return response.json()

def fetch_genre_ids():
    """Fetch the list of genres and their IDs from the Watchmode API."""
    url = f"{BASE_URL}/genres/"
    params = {"apiKey": WATCHMODE_API_KEY.strip()}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {genre['name'].lower(): genre['id'] for genre in data}  # Map genre names to IDs
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching genre IDs: {e}")
        return {}

# Genre mapping for books for each MBTI type
mbti_book_genre_keywords = {
    'INTJ': ['philosophy', 'strategy', 'politics', 'technology', 'non-fiction'],
    'INFJ': ['self-help', 'spirituality', 'psychology', 'poetry', 'fiction'],
    'ENFP': ['creativity', 'self-help', 'psychology', 'adventure', 'fiction'],
    'ENTP': ['innovation', 'philosophy', 'entrepreneurship', 'debate', 'science'],
    'ISFJ': ['historical fiction', 'family', 'romance', 'biography', 'self-help'],
    'ISTJ': ['non-fiction', 'history', 'biography', 'law', 'economics'],
    'ESFP': ['entertainment', 'comedy', 'romance', 'travel', 'music'],
    'ESTP': ['adventure', 'action', 'thriller', 'sports', 'mystery'],
    'ISFP': ['art', 'romance', 'nature', 'music', 'fiction'],
    'INFP': ['self-help', 'spirituality', 'fantasy', 'poetry', 'fiction'],
    'ESFJ': ['romance', 'historical fiction', 'family', 'drama', 'relationships'],
    'ESTJ': ['economics', 'self-help', 'history', 'leadership', 'law'],
    'ENFJ': ['self-help', 'psychology', 'education', 'inspiration', 'romance'],
    'ENTJ': ['strategy', 'leadership', 'non-fiction', 'technology', 'philosophy'],
    'ISTP': ['engineering', 'thriller', 'science', 'mystery', 'action'],
    'INTP': ['philosophy', 'psychology', 'technology', 'fantasy', 'science']
}

# Genre mapping for songs for each MBTI type
mbti_song_genre_keywords = {
    'INTJ': ['classical', 'instrumental', 'ambient', 'electronic', 'jazz'],
    'INFJ': ['indie', 'folk', 'acoustic', 'ambient', 'classical'],
    'ENFP': ['pop', 'indie', 'dance', 'electronic', 'alternative'],
    'ENTP': ['rock', 'alternative', 'electronic', 'jazz', 'experimental'],
    'ISFJ': ['acoustic', 'classical', 'romantic', 'folk', 'soft rock'],
    'ISTJ': ['classical', 'instrumental', 'jazz', 'blues', 'orchestral'],
    'ESFP': ['pop', 'dance', 'hip-hop', 'party', 'electronic'],
    'ESTP': ['rock', 'hip-hop', 'electronic', 'dance', 'pop'],
    'ISFP': ['indie', 'folk', 'acoustic', 'romantic', 'soft rock'],
    'INFP': ['indie', 'folk', 'acoustic', 'ambient', 'alternative'],
    'ESFJ': ['pop', 'romantic', 'dance', 'party', 'soft rock'],
    'ESTJ': ['rock', 'classical', 'jazz', 'instrumental', 'orchestral'],
    'ENFJ': ['pop', 'indie', 'romantic', 'dance', 'alternative'],
    'ENTJ': ['rock', 'electronic', 'jazz', 'instrumental', 'experimental'],
    'ISTP': ['rock', 'alternative', 'electronic', 'jazz', 'blues'],
    'INTP': ['ambient', 'experimental', 'electronic', 'jazz', 'instrumental']
}

# Genre mapping for movies for each MBTI type
mbti_movie_genre_keywords = {
    'INTJ': ['science fiction', 'mystery', 'thriller', 'drama', 'adventure'],
    'INFJ': ['fantasy', 'psychological', 'romance', 'biography', 'animation'],
    'ENFP': ['comedy', 'adventure', 'fantasy', 'romance', 'action'],
    'ENTP': ['science fiction', 'action', 'adventure', 'comedy', 'thriller'],
    'ISFJ': ['family', 'romance', 'historical', 'drama', 'biography'],
    'ISTJ': ['history', 'crime', 'drama', 'mystery', 'war'],
    'ESFP': ['comedy', 'romance', 'music', 'adventure', 'family'],
    'ESTP': ['action', 'thriller', 'adventure', 'sports', 'crime'],
    'ISFP': ['romance', 'drama', 'art', 'nature', 'music'],
    'INFP': ['fantasy', 'romance', 'drama', 'adventure', 'animation'],
    'ESFJ': ['romance', 'family', 'drama', 'comedy', 'relationships'],
    'ESTJ': ['history', 'crime', 'war', 'politics', 'economics'],  # Replaced "leadership" and "strategy"
    'ENFJ': ['inspirational', 'romance', 'drama', 'education', 'psychological'],
    'ENTJ': ['action', 'thriller', 'science fiction', 'war', 'politics'],  # Replaced "strategy"
    'ISTP': ['thriller', 'action', 'mystery', 'adventure', 'crime'],
    'INTP': ['science fiction', 'fantasy', 'mystery', 'psychological', 'adventure']
}

# Corrected function to fetch books from Open Library
def get_books_by_mbti_and_genre(mbti_type, genre):
    """Fetch books from Open Library based on the MBTI type and genre."""
    if mbti_type not in mbti_book_genre_keywords:
        st.error("Invalid MBTI type. Please provide a valid MBTI type.")
        return []

    if genre not in mbti_book_genre_keywords[mbti_type]:
        st.warning(f"Genre '{genre}' is not a typical genre for {mbti_type}.")
        return []

    query = f'{genre}'  # Use only the genre for a broader search
    url = f'https://openlibrary.org/search.json?q={query}&limit=10'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching book data: {e}")
        return []

    if 'docs' not in data or not data['docs']:
        st.error(f"No books found for MBTI type: {mbti_type} with genre: {genre}")
        return []

    books = []
    for book in data['docs'][:5]:  # Limit to the first 6 books
        title = book.get('title', 'Unknown Title')
        authors = book.get('author_name', ['Unknown Author'])
        cover_id = book.get('cover_i')  # Use 'cover_i' for cover images
        cover_url = f'https://covers.openlibrary.org/b/id/{cover_id}-L.jpg' if cover_id else None
        books.append({
            'title': title,
            'authors': ', '.join(authors),
            'cover_url': cover_url or 'No cover image available',
            'genre': genre
        })

    return books

# Corrected function to display books
def display_books(books):
    """Display books with their details."""
    for book in books:
        st.write(f"*Title:* {book['title']}")
        st.write(f"*Authors:* {book['authors']}")
        st.write(f"*Genre:* {book['genre']}")
        if book['cover_url'] != 'No cover image available':
            st.image(book['cover_url'], caption=book['title'])
        else:
            st.write(book['cover_url'])
        st.markdown("---")

# Function to display movies
def display_movies(movies):
    """Display up to 5 movies with their details."""
    for movie in movies[:5]:  # Limit to the first 5 movies
        st.write(f"*Title:* {movie['title']}")
        st.write(f"*Release Date:* {movie['release_date']}")
        st.markdown("---")

# Corrected Streamlit app
def main():
    st.title("MBTI Personality Test and Media Recommendations")

    # Initialize session state
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
        st.session_state.answers = []
        st.session_state.questions = load_questions()
        st.session_state.refresh = False  # Add a refresh flag


    # App title and instructions with enforced white background
    st.markdown(
        """
        <style>
            /* Set the background color for the entire page */
            html, body, [data-testid="stAppViewContainer"] {
                background-color: white !important;
                color: black !important;
            }
            .title {
                text-align: center; /* Center-align the title */
                color: #4CAF50;
                font-size: 36px;
                font-family: 'Arial', sans-serif;
                margin-top: 20px; /* Add some spacing above the title */
            }
            .instructions {
                text-align: center;
                font-size: 18px;
                color: #555;
                font-family: 'Arial', sans-serif;
            }
            .stButton>button {
                background-color: #0E1117;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 8px;
            }
            .stButton>button:hover {
                background-color: #45a049;
            }
        </style>
        <div>
            <h1 class="title">🎭 M.B.E.R.S 🎭</h1>
            <p class="instructions">Click on a button to select your answer (1 = Strongly Disagree, 7 = Strongly Agree).</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display the current question
    questions = st.session_state.questions
    current_question_index = st.session_state.current_question

    if current_question_index < len(questions):
        question, category, weight = questions[current_question_index]
    
        # Display question number and question text
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <h3 style="color: #2196F3; font-family: 'Arial', sans-serif;">Q{current_question_index + 1}:</h3>
                <h3 style="color: #333; font-family: 'Arial', sans-serif;">{question}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    
        # Display buttons for answers (1 to 7)
        st.write("Select your answer:")
        cols = st.columns(7)
        for i in range(1, 8):  # Buttons for 1 to 7
            if cols[i - 1].button(str(i), key=f"button_{current_question_index}_{i}"):
                st.session_state.answers.append(i)
                st.session_state.current_question += 1
                st.session_state.refresh = not st.session_state.refresh  # Toggle the refresh flag
    else:
        # Calculate MBTI type
        mbti_result = calculate_mbti(st.session_state.answers, questions)
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 30px;">
                <h2 style="color: #4CAF50; font-family: 'Arial', sans-serif;">Your MBTI Personality Type: {mbti_result}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Media Recommendations Section
        st.header("Media Recommendations Based on Your MBTI Type")

        # Song Recommendations
        st.subheader("Spotify Tracks")

        # Use the calculated MBTI type directly
        mbti_type = mbti_result

        # Display genres for the calculated MBTI type
        if mbti_type in mbti_song_genre_keywords:
            genre = st.selectbox("Select a genre", mbti_song_genre_keywords[mbti_type], key="song_genre_selectbox")

            if st.button("Get Song Recommendations", key="song_recommendation_button"):
                song_query = f"{genre} music"
                track_details = search_spotify_songs(song_query)

                if track_details:
                    for track in track_details:
                        st.write(f"**Track**: {track['name']} by {track['artist']}")
                        st.image(track['image_url'], width=150)
                        st.write(f"[Listen on Spotify]({track['spotify_url']})")
                        st.write("---")
                else:
                    st.write("No songs found for the selected MBTI type and genre.")
        else:
            st.error("Invalid MBTI type. Unable to fetch song recommendations.")

        # Movie Recommendations
        st.subheader("Movies")

        # Use the calculated MBTI type directly
        mbti_type = mbti_result

        # Display genres for the calculated MBTI type
        if mbti_type in mbti_movie_genre_keywords:
            genre = st.selectbox("Select a genre", mbti_movie_genre_keywords[mbti_type], key="movie_genre_selectbox")

            if st.button("Get Movie Recommendations", key="movie_recommendation_button"):
                movies = search_watchmode_movies(genre)

                if movies:
                    # Display the movies with poster images (if available)
                    display_movies(movies)
                else:
                    st.write("No movies found for the selected MBTI type and genre.")
        else:
            st.error("Invalid MBTI type. Unable to fetch movie recommendations.")
        
        # Book Recommendations
        st.subheader("Books")

        # Use the calculated MBTI type directly
        mbti_type = mbti_result

        # Display genres for the calculated MBTI type
        if mbti_type in mbti_book_genre_keywords:
            genre = st.selectbox("Select a genre", mbti_book_genre_keywords[mbti_type], key="book_genre_selectbox")

            if st.button("Get Book Recommendations", key="book_recommendation_button"):
                books = get_books_by_mbti_and_genre(mbti_type, genre)

                if books:
                    # Display the books with cover images (if available)
                    display_books(books)
                else:
                    st.write("No books found for the selected MBTI type and genre.")
        else:
            st.error("Invalid MBTI type. Unable to fetch book recommendations.")

        # Restart option
        if st.button("Restart Test"):
            st.session_state.current_question = 0
            st.session_state.answers = []
            st.session_state.questions = load_questions()
            st.session_state.refresh = not st.session_state.refresh  # Toggle the refresh flag

if __name__ == "__main__":
    main()
