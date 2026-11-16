import re
import string

# Core English stop words tailored for lost-and-found descriptions
DEFAULT_STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
    "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
    'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
    'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
    'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
    'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can',
    'will', 'just', 'should', "now", 'lost', 'found', 'please', 'help', 'someone',
    'kindly', 'item', 'belonging', 'contact', 'yesterday', 'today', 'morning', 'evening'
}

# Common noun plural endings normalization
def simple_stem(word: str) -> str:
    """Normalize simple English plurals and common inflections without heavy external libraries."""
    w = word.strip().lower()
    if len(w) <= 3:
        return w
    if w.endswith('ies') and len(w) > 4:
        return w[:-3] + 'y'
    if w.endswith(('sses', 'shes', 'ches', 'xes', 'zes')) and len(w) > 4:
        return w[:-2]
    if w.endswith('s') and not w.endswith('ss') and len(w) > 3:
        return w[:-1]
    return w


def preprocess_text(text: str, remove_stopwords: bool = True) -> str:
    """
    Cleans, normalizes, and pre-processes raw user text input.
    - Lowers case
    - Removes punctuation, symbols, and redundant whitespaces
    - Optionally removes generic stop words
    - Applies light inflection normalization
    """
    if not text:
        return ""
    
    # Lowercase
    cleaned = text.lower()
    
    # Replace punctuation and special characters with spaces
    cleaned = re.sub(f'[{re.escape(string.punctuation)}0-9]', ' ', cleaned)
    
    # Tokenize by whitespace
    tokens = cleaned.split()
    
    processed_tokens = []
    for token in tokens:
        token = token.strip()
        if not token or len(token) < 2:
            continue
        if remove_stopwords and token in DEFAULT_STOP_WORDS:
            continue
        stemmed = simple_stem(token)
        processed_tokens.append(stemmed)
        
    return " ".join(processed_tokens)


def build_item_text_corpus(item_name: str, category: str, description: str, 
                           location: str = "", additional_details: str = "") -> str:
    """
    Constructs a weighted textual representation of a lost/found item.
    Item name is repeated twice to give higher emphasis in TF-IDF.
    """
    name_part = f"{item_name or ''} {item_name or ''}"
    cat_part = f"{category or ''}"
    desc_part = f"{description or ''}"
    loc_part = f"{location or ''}"
    extra_part = f"{additional_details or ''}"
    
    full_text = f"{name_part} {cat_part} {desc_part} {loc_part} {extra_part}"
    return preprocess_text(full_text)
