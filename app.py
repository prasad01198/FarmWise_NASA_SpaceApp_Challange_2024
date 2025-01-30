from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import logging
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
import io
import base64

app = Flask(__name__)
app.secret_key = 'YOUR_SECRET_KEY'  # Required for flash messages

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    if request.method == 'POST':
        data_type = request.form.get('data-type')
        location = request.form.get('location')
        start_date = request.form.get('start-date')
        end_date = request.form.get('end-date')

        # Validate inputs
        if not location or not start_date or not end_date:
            flash('Please fill in all fields.')
            return redirect(url_for('home'))

        # Construct the command based on the selected data type
        if data_type == '1':
            script = 'data_scripts/soil_data.py'
        elif data_type == '2':
            script = 'data_scripts/rain_data.py'
        elif data_type == '3':
            script = 'data_scripts/weather_data.py'  # Add this line for weather data
        else:
            flash('Invalid data type selected!')
            return redirect(url_for('home'))

        # Execute the script and capture the output
        try:
            result = subprocess.run(['python', script, location, start_date, end_date],
                                    check=True, capture_output=True, text=True)
            flash('Data fetched successfully!')
            logging.info(f'Data fetched successfully from {script}')
            return redirect(url_for('visualize_data', data_type=data_type))
        except subprocess.CalledProcessError as e:
            flash(f'An error occurred: {e.stderr}')
            logging.error(f'Error executing {script}: {e.stderr}')
        
        return redirect(url_for('home'))

@app.route('/visualize_data/<data_type>')
def visualize_data(data_type):
    if data_type == '1':
        csv_file = 'soil_moisture_data.csv'
    elif data_type == '2':
        csv_file = 'rainfall_data.csv'
    else:
        flash('Invalid data type for visualization!')
        return redirect(url_for('home'))

    if os.path.exists(csv_file):
        # Read the data
        df = pd.read_csv(csv_file)

        # Print the columns for debugging
        logging.info(f"Columns in the CSV: {df.columns.tolist()}")
        logging.info(f"Sample data: {df.head()}")

        # Extract average values
        df['avg_value'] = df['value'].apply(lambda x: eval(x)['avg'])  # Extract 'avg' from 'value'
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y')  # Ensure 'date' is in datetime format

        # Create visualizations
        images = {}

        # Visualizations for Soil Moisture
        if data_type == '1':
            # Average Soil Moisture Over Time
            fig1 = px.line(df, x='date', y='avg_value', title='Average Soil Moisture Over Time',
                           labels={'avg_value': 'Average Soil Moisture (%)'},
                           template='plotly_white')
            images['line_plot'] = base64.b64encode(pio.to_image(fig1, format='png')).decode('utf8')

            # Soil Moisture Scatter Plot
            fig2 = px.scatter(df, x='date', y='avg_value', title='Soil Moisture Scatter Plot',
                              labels={'avg_value': 'Average Soil Moisture (%)'},
                              template='plotly_white')
            images['scatter_plot'] = base64.b64encode(pio.to_image(fig2, format='png')).decode('utf8')

            # Distribution of Soil Moisture Values
            fig3 = px.histogram(df, x='avg_value', nbins=10, title='Distribution of Soil Moisture Values',
                                 labels={'avg_value': 'Soil Moisture (%)'},
                                 template='plotly_white')
            images['histogram'] = base64.b64encode(pio.to_image(fig3, format='png')).decode('utf8')

            # Soil Moisture Value Distribution
            fig4 = px.box(df, y='avg_value', title='Soil Moisture Value Distribution',
                          labels={'avg_value': 'Average Soil Moisture (%)'},
                          template='plotly_white')
            images['box_plot'] = base64.b64encode(pio.to_image(fig4, format='png')).decode('utf8')

        # Visualizations for Rainfall
        elif data_type == '2':
            # Average Rainfall Over Time
            fig5 = px.line(df, x='date', y='avg_value', title='Average Rainfall Over Time',
                           labels={'avg_value': 'Average Rainfall (mm)'},
                           template='plotly_white')
            images['line_plot'] = base64.b64encode(pio.to_image(fig5, format='png')).decode('utf8')

            # Rainfall Scatter Plot
            fig6 = px.scatter(df, x='date', y='avg_value', title='Rainfall Scatter Plot',
                              labels={'avg_value': 'Average Rainfall (mm)'},
                              template='plotly_white')
            images['scatter_plot'] = base64.b64encode(pio.to_image(fig6, format='png')).decode('utf8')

            # Distribution of Rainfall Values
            fig7 = px.histogram(df, x='avg_value', nbins=10, title='Distribution of Rainfall Values',
                                labels={'avg_value': 'Rainfall (mm)'},
                                template='plotly_white')
            images['histogram'] = base64.b64encode(pio.to_image(fig7, format='png')).decode('utf8')

            # Rainfall Value Distribution
            fig8 = px.box(df, y='avg_value', title='Rainfall Value Distribution',
                          labels={'avg_value': 'Average Rainfall (mm)'},
                          template='plotly_white')
            images['box_plot'] = base64.b64encode(pio.to_image(fig8, format='png')).decode('utf8')

        # Summary statistics
        summary_stats = {
            'Average Value': df['avg_value'].mean(),
            'Max Value': df['avg_value'].max(),
            'Min Value': df['avg_value'].min()
        }

        return render_template('visualization.html', data_type=data_type, summary_stats=summary_stats, images=images)
    else:
        flash('Data file not found!')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
