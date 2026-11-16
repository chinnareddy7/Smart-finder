from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ai_engine.preprocessing import build_item_text_corpus, preprocess_text

class RealAIMatchingEngine:
    """
    Production-grade AI Matching Engine for Campus Lost & Found System.
    Combines:
    1. Scikit-learn TF-IDF Vectorization with unigrams & bigrams.
    2. Cosine Similarity measurement on preprocessed semantic text.
    3. Category compatibility comparison.
    4. Campus location proximity & keyword overlap matching.
    """
    
    def __init__(self, text_weight: float = 0.60, category_weight: float = 0.25, location_weight: float = 0.15):
        self.text_weight = text_weight
        self.category_weight = category_weight
        self.location_weight = location_weight

    def compare_categories(self, cat1: str, cat2: str) -> tuple[float, bool]:
        """Compares categories and returns (score, is_exact_match)."""
        if not cat1 or not cat2:
            return 0.0, False
            
        c1 = cat1.strip().lower()
        c2 = cat2.strip().lower()
        
        if c1 == c2:
            return 1.0, True
            
        # Check partial compatibility
        tokens1 = set(preprocess_text(c1).split())
        tokens2 = set(preprocess_text(c2).split())
        if tokens1 and tokens2 and (tokens1 & tokens2):
            return 0.6, False
            
        return 0.0, False

    def compare_locations(self, loc1: str, loc2: str) -> tuple[float, bool]:
        """Compares locations and returns (score, is_exact_match)."""
        if not loc1 or not loc2:
            return 0.1, False
            
        l1 = loc1.strip().lower()
        l2 = loc2.strip().lower()
        
        if l1 == l2:
            return 1.0, True
            
        # Substring or token overlap (e.g. 'library', 'lab', 'canteen')
        tokens1 = set(preprocess_text(l1).split())
        tokens2 = set(preprocess_text(l2).split())
        if tokens1 and tokens2:
            intersection = tokens1 & tokens2
            if intersection:
                return 0.75, False
                
        return 0.1, False

    def extract_shared_keywords(self, text1: str, text2: str) -> list[str]:
        """Finds meaningful shared words between two preprocessed texts."""
        tokens1 = set(preprocess_text(text1).split())
        tokens2 = set(preprocess_text(text2).split())
        common = sorted(list(tokens1 & tokens2))
        return common

    def compute_similarity(self, lost_item, found_item) -> dict:
        """
        Computes the complete AI similarity score between a LostItem and a FoundItem.
        Returns a dictionary with comprehensive scores, boolean flags, and explanation.
        """
        # 1. Build text representations
        lost_corpus = build_item_text_corpus(
            lost_item.item_name,
            lost_item.category,
            lost_item.description,
            lost_item.location,
            getattr(lost_item, 'additional_details', '') or ''
        )
        
        found_corpus = build_item_text_corpus(
            found_item.item_name,
            found_item.category,
            found_item.description,
            found_item.location,
            getattr(found_item, 'additional_details', '') or ''
        )
        
        # 2. Scikit-learn TF-IDF Vectorizer and Cosine Similarity
        text_score = 0.0
        shared_keywords = []
        
        # Guard against completely empty corpora
        if lost_corpus.strip() and found_corpus.strip():
            try:
                # Use unigrams and bigrams to capture compound phrases
                vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
                tfidf_matrix = vectorizer.fit_transform([lost_corpus, found_corpus])
                sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                cosine_val = float(sim_matrix[0][0])
                # Ensure bounded [0, 1]
                text_score = max(0.0, min(1.0, cosine_val))
                
                shared_keywords = self.extract_shared_keywords(
                    f"{lost_item.item_name} {lost_item.description}",
                    f"{found_item.item_name} {found_item.description}"
                )
            except Exception:
                text_score = 0.0
        else:
            text_score = 0.0

        # 3. Category comparison
        cat_score, cat_match = self.compare_categories(lost_item.category, found_item.category)
        
        # 4. Location comparison
        loc_score, loc_match = self.compare_locations(lost_item.location, found_item.location)
        
        # 5. Weighted overall score calculation (percentage 0.0 to 100.0)
        overall_score = (
            (text_score * self.text_weight) +
            (cat_score * self.category_weight) +
            (loc_score * self.location_weight)
        ) * 100.0
        
        # Round scores
        overall_score = round(max(0.0, min(100.0, overall_score)), 1)
        text_percent = round(text_score * 100.0, 1)
        cat_percent = round(cat_score * 100.0, 1)
        loc_percent = round(loc_score * 100.0, 1)

        # 6. Generate human-understandable explanation
        explanation_points = []
        if cat_match:
            explanation_points.append(f"Category matches exactly ({lost_item.category}).")
        elif cat_score > 0:
            explanation_points.append(f"Categories share related terms ({lost_item.category} / {found_item.category}).")
        else:
            explanation_points.append(f"Different categories reported.")
            
        if loc_match:
            explanation_points.append(f"Reported in the identical campus location ({lost_item.location}).")
        elif loc_score > 0.5:
            explanation_points.append(f"Reported in nearby campus zones ({lost_item.location} vs {found_item.location}).")
            
        if shared_keywords:
            keywords_preview = ", ".join(f"'{k}'" for k in shared_keywords[:5])
            explanation_points.append(f"Key matching terms: {keywords_preview}.")
            
        if overall_score >= 75.0:
            confidence = "High confidence match"
        elif overall_score >= 50.0:
            confidence = "Moderate probability match"
        else:
            confidence = "Low to fair similarity"
            
        explanation = f"{confidence}: " + " ".join(explanation_points)
        
        return {
            'overall_score': overall_score,
            'text_score': text_percent,
            'category_score': cat_percent,
            'location_score': loc_percent,
            'category_match': cat_match,
            'location_match': loc_match,
            'shared_keywords': shared_keywords,
            'explanation': explanation
        }


# Global instance
ai_engine = RealAIMatchingEngine()


def sync_matches_for_lost_item(db, lost_item, threshold: float = 25.0, top_limit: int = 5):
    """
    Evaluates the newly reported or updated LostItem against all active FoundItems,
    stores or updates the top matches in the database, and creates notifications.
    """
    from models import FoundItem, Match, Notification
    
    # Query all active found items
    active_founds = FoundItem.query.filter(
        FoundItem.status != 'Claimed'
    ).all()
    
    scored_candidates = []
    for found in active_founds:
        # Avoid comparing an item reported by the exact same user if it's the exact same item
        res = ai_engine.compute_similarity(lost_item, found)
        if res['overall_score'] >= threshold:
            scored_candidates.append((found, res))
            
    # Sort descending by overall similarity
    scored_candidates.sort(key=lambda x: x[1]['overall_score'], reverse=True)
    top_candidates = scored_candidates[:top_limit]
    
    created_or_updated_matches = []
    
    for found, res in top_candidates:
        match_record = Match.query.filter_by(
            lost_item_id=lost_item.id,
            found_item_id=found.id
        ).first()
        
        if not match_record:
            match_record = Match(
                lost_item_id=lost_item.id,
                found_item_id=found.id
            )
            db.session.add(match_record)
            
        match_record.similarity_score = res['overall_score']
        match_record.text_score = res['text_score']
        match_record.category_score = res['category_score']
        match_record.location_score = res['location_score']
        match_record.category_match = res['category_match']
        match_record.location_match = res['location_match']
        match_record.explanation = res['explanation']
        match_record.status = 'Suggested'
        
        created_or_updated_matches.append(match_record)
        
        # If score is >= 40%, send notification to lost item owner
        if res['overall_score'] >= 40.0:
            notif_title = f"AI Match Found: {res['overall_score']}% Match!"
            notif_msg = f"Our AI detected a potential match for your lost '{lost_item.item_name}' with a found '{found.item_name}'."
            # Check if recent notification already exists to avoid spam
            existing_notif = Notification.query.filter_by(
                user_id=lost_item.user_id,
                title=notif_title,
                is_read=False
            ).first()
            if not existing_notif:
                notif = Notification(
                    user_id=lost_item.user_id,
                    title=notif_title,
                    message=notif_msg,
                    notification_type='match_found',
                    link=f"/matches"
                )
                db.session.add(notif)
                
    db.session.commit()
    return created_or_updated_matches


def sync_matches_for_found_item(db, found_item, threshold: float = 25.0, top_limit: int = 5):
    """
    Evaluates the newly reported or updated FoundItem against all active LostItems,
    stores or updates the top matches in the database, and creates notifications.
    """
    from models import LostItem, Match, Notification
    
    active_losts = LostItem.query.filter(
        LostItem.status != 'Recovered'
    ).all()
    
    scored_candidates = []
    for lost in active_losts:
        res = ai_engine.compute_similarity(lost, found_item)
        if res['overall_score'] >= threshold:
            scored_candidates.append((lost, res))
            
    scored_candidates.sort(key=lambda x: x[1]['overall_score'], reverse=True)
    top_candidates = scored_candidates[:top_limit]
    
    created_or_updated_matches = []
    
    for lost, res in top_candidates:
        match_record = Match.query.filter_by(
            lost_item_id=lost.id,
            found_item_id=found_item.id
        ).first()
        
        if not match_record:
            match_record = Match(
                lost_item_id=lost.id,
                found_item_id=found_item.id
            )
            db.session.add(match_record)
            
        match_record.similarity_score = res['overall_score']
        match_record.text_score = res['text_score']
        match_record.category_score = res['category_score']
        match_record.location_score = res['location_score']
        match_record.category_match = res['category_match']
        match_record.location_match = res['location_match']
        match_record.explanation = res['explanation']
        match_record.status = 'Suggested'
        
        created_or_updated_matches.append(match_record)
        
        # Notify lost item owner
        if res['overall_score'] >= 40.0:
            notif_title = f"AI Match Found: {res['overall_score']}% Match!"
            notif_msg = f"A newly reported found item '{found_item.item_name}' matches your lost report for '{lost.item_name}'."
            existing_notif = Notification.query.filter_by(
                user_id=lost.user_id,
                title=notif_title,
                is_read=False
            ).first()
            if not existing_notif:
                notif = Notification(
                    user_id=lost.user_id,
                    title=notif_title,
                    message=notif_msg,
                    notification_type='match_found',
                    link=f"/matches"
                )
                db.session.add(notif)
                
    db.session.commit()
    return created_or_updated_matches


def recalculate_all_matches(db, threshold: float = 25.0):
    """
    Recalculates all AI similarity scores for all unresolved lost and found items.
    """
    from models import LostItem, FoundItem, Match
    
    active_losts = LostItem.query.filter(LostItem.status != 'Recovered').all()
    active_founds = FoundItem.query.filter(FoundItem.status != 'Claimed').all()
    
    count = 0
    for lost in active_losts:
        for found in active_founds:
            res = ai_engine.compute_similarity(lost, found)
            if res['overall_score'] >= threshold:
                match_rec = Match.query.filter_by(
                    lost_item_id=lost.id,
                    found_item_id=found.id
                ).first()
                if not match_rec:
                    match_rec = Match(
                        lost_item_id=lost.id,
                        found_item_id=found.id
                    )
                    db.session.add(match_rec)
                    
                match_rec.similarity_score = res['overall_score']
                match_rec.text_score = res['text_score']
                match_rec.category_score = res['category_score']
                match_rec.location_score = res['location_score']
                match_rec.category_match = res['category_match']
                match_rec.location_match = res['location_match']
                match_rec.explanation = res['explanation']
                count += 1
                
    db.session.commit()
    return count
