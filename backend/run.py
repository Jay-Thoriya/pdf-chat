from app import create_app  # Import the create_app function

app = create_app()  # Get the app instance from create_app function

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app with debugging enabled
