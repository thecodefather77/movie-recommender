import os
import streamlit as st
import pickle
import requests
from dotenv import load_dotenv
load_dotenv()

# Page Setup
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# Fetch API Key
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if TMDB_API_KEY is None:
    try:
        TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
    except Exception:
        TMDB_API_KEY = None

# Read the Pickle File and Cache it so it does not load on every rerun
@st.cache_resource
def load_data():
    movies_df = pickle.load(open('movies.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies_df, similarity

movies_df, similarity = load_data()


# Recommend Function
def recommend(movie):
    # Fetch the index of the movie for which we want the recommendations
    movie_index = movies_df[(movies_df['Title'] == movie)].index[0]
    # Fetch the similarity list from the similarity matrix
    distances = similarity[movie_index]
    # Sort the enumerated (To keep the TMDB Movie Id intact) list
    # And fetch only thr top 5 recommendations except the first one (The wanted movie itself)
    movies_list = sorted(
        list(enumerate(distances)),
        key = lambda x: x[1],
        reverse = True
    )[1:11]

    recommend_movies = []
    recommend_movies_poster = []
    for i in movies_list:
        # Fetch the TMDB Movie ID (To Fetch the Poster)
        movie_id = movies_df.iloc[i[0]]['ID']
        # Appedn the Recommended Movies Names
        recommend_movies.append(movies_df.iloc[i[0]]['Title'])
        # Fetch Poster From TMDB API
        recommend_movies_poster.append(fetch_poster(movie_id))

    # Return the appended list of recommended movie names and posters  
    return recommend_movies, recommend_movies_poster

# Poster Fetch Function using TMDB API
# Cache API Calls
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    # If No API Key Available
    if not TMDB_API_KEY:
        return "https://dummyimage.com/500x750/455c73/ffffff&text=No+API+Key"
    
    # If API Key is available
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        # Get response from TNDB
        response = requests.get(url, timeout = 10)
        response.raise_for_status()
        # Store the data as json
        data = response.json()

        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500" + poster_path
        else:
            return "https://dummyimage.com/500x750/455c73/ffffff&text=Error"
    
    except requests.exceptions.RequestException as e:
        print(f"Connection Error: {e}")
        return "https://dummyimage.com/500x750/455c73/ffffff&text=Error"

# Title of the Website
st.title('Movie Recommender System')

# Movie Selector
selected_movie_name = st.selectbox(
    'Select a Movie',
    movies_df['Title']
)

# Recommed Button
if st.button('Recommend'):
    with st.spinner("Fetching Recommendations..."):
        names, posters = recommend(selected_movie_name)
        
        with st.container():
            # Create a new row of columns for every 5 movies
            for i in range(0, len(names), 5):
                cols = st.columns(5)
                
                # Slice the names and posters for just this row (eg: 0-5, 0-15)
                row_names = names[i : i + 5]
                row_posters = posters[i : i + 5]
                
                for j in range(len(row_names)):
                    with cols[j]:
                        # use_container_width ensures images fill the column evenly
                        st.image(row_posters[j], use_container_width=True)
                        st.caption(row_names[j])

st.markdown(
    "---\nBuilt using Streamlit and TMDB API",
    unsafe_allow_html = True
)