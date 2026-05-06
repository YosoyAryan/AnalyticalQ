import os
import pandas as pd
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .forms import UploadCSVForm

# Temporary in-memory storage for uploaded data
DATA_STORAGE = {}

def home(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(csv_file.name, csv_file)
            file_path = fs.path(filename)

            try:
                df = pd.read_csv(file_path)
                DATA_STORAGE['df'] = df
                return redirect('options')
            except Exception as e:
                return render(request, 'dashboard/home.html', {
                    'form': form,
                    'error': f"Error reading CSV: {e}"
                })
    else:
        form = UploadCSVForm()

    return render(request, 'dashboard/home.html', {'form': form})


def options(request):
    if 'df' not in DATA_STORAGE:
        return redirect('home')
    return render(request, 'dashboard/options.html')


def visualize_data(request):
    from .ai_tools import query_data
    if request.method == 'POST':
        query = request.POST.get('query')
        df = DATA_STORAGE.get('df')
        if df is not None:
            result = query_data(df, query)
            return render(request, 'dashboard/visualize_result.html', {
                'query': query,
                'plot_path': result.get('plot_path'),
                'explanation': result.get('explanation'),
                'code': result.get('code'),
            })
    return redirect('options')



def get_insights(request):
    from .ai_tools import analyze_data_with_ai_and_visualize, get_insights_from_llm_with_visualization
    if request.method == 'POST':
        query = request.POST.get('query')
        df = DATA_STORAGE.get('df')
        if df is not None:
            insights = analyze_data_with_ai_and_visualize(df)
            target_column = insights.get("target_column", "")
            
            # 🛠️ Clean up target_column if needed
            if isinstance(target_column, str) and target_column.strip().startswith("The best"):
                import re
                match = re.search(r"\*\*(.*?)\*\*", target_column)
                if match:
                    target_column = match.group(1).strip()

            try:
                insight_text = get_insights_from_llm_with_visualization(insights, df, query)
                if isinstance(insight_text, list):
                    insight_text = "\n\n".join(str(i) for i in insight_text)
                elif not isinstance(insight_text, str):
                    insight_text = str(insight_text)
            except Exception as e:
                insight_text = f"Error generating insights: {e}"

            return render(request, 'dashboard/insight_result.html', {
                'query': query,
                'insight_text': insight_text,
                'target_column': target_column
            })
    return redirect('options')


def perform_analysis(request):
    from .ai_tools import perform_analysis
    if request.method == 'POST':
        query = request.POST.get('query')
        analysis_type = request.POST.get('analysis_type')
        df = DATA_STORAGE.get('df')
        if df is not None:
            try:
                result_text = perform_analysis(df, query, analysis_type)
                if isinstance(result_text, list):
                    result_text = "\n\n".join(str(i) for i in result_text)
                elif not isinstance(result_text, str):
                    result_text = str(result_text)
            except Exception as e:
                result_text = f"Error performing analysis: {e}"

            return render(request, 'dashboard/analysis_result.html', {
                'query': query,
                'analysis_type': analysis_type,
                'result_text': result_text
            })
    return redirect('options')
