from app import create_app
from app.db import db
from sqlalchemy import text

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Dropping old model_predictions table...")
        db.session.execute(text("DROP TABLE IF EXISTS model_predictions"))
        db.session.commit()
        
        print("Creating new model_predictions table...")
        from app.models import ModelPrediction
        db.create_all()
        
        print("Migration completed successfully!")
        print("New columns: predicted_popularity, predicted_vote_average, actual_popularity, actual_vote_average, mae_popularity, mae_vote_average")


