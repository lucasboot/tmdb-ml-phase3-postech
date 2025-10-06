from app import create_app
from app.db import db
from app.models import (
    HorrorRegression,
    HorrorRegressionPrediction,
    HorrorClassification,
    HorrorClustering,
    HorrorClusterProfile
)

def migrate_horror_tables():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ Tabelas de análise de terror criadas com sucesso!")
        print("   - horror_regression")
        print("   - horror_regression_predictions")
        print("   - horror_classification")
        print("   - horror_clustering")
        print("   - horror_cluster_profiles")

if __name__ == "__main__":
    migrate_horror_tables()


