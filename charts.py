"""Plotly charts đơn giản, dùng lại cho 4 trang."""
import plotly.graph_objects as go
import plotly.express as px

# Palette thống nhất với ảnh mẫu: Navy / Sky Blue / Warm Orange / Pastel.
BLUE='#4D93EE'
TEAL=BLUE  # Tương thích các biểu đồ cũ; không dùng xanh teal lệch màu mẫu
NAVY='#142943'
ORANGE='#FFAD51'
GREY='#E8EEF8'
PALETTE=[BLUE,ORANGE,'#3C78C7','#FFC47D','#85BBF5','#EA9C50']


def style(fig, height=370):
    fig.update_layout(
        height=height, margin=dict(l=8,r=24,t=20,b=12),
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif',size=12,color=NAVY),
        hoverlabel=dict(bgcolor='white',font_size=12),
        xaxis=dict(showgrid=True,gridcolor='#E8EEF8',zeroline=False),
        yaxis=dict(showgrid=False),showlegend=False
    )
    return fig


def bars(df, dimension, metric='rate', height=350, color=TEAL):
    df=df.sort_values(metric,ascending=True).copy()
    if metric=='rate':
        units='%' ; vals=[f'{v:.2f}%' for v in df.rate]
        title='Tỷ lệ hoàn trả (%)'
    else:
        units=' đơn'; vals=[f'{int(v):,}' for v in df.returns]
        title='Số đơn hoàn trả'
    colors=[color]*len(df)
    if colors: colors[-1]=ORANGE
    fig=go.Figure(go.Bar(y=df[dimension],x=df[metric],orientation='h',marker_color=colors,
        customdata=df[['orders','returns','rate']].to_numpy(),
        hovertemplate='<b>%{y}</b><br>Tổng đơn: %{customdata[0]:,.0f}<br>Hoàn trả: %{customdata[1]:,.0f}<br>Tỷ lệ: %{customdata[2]:.2f}%<extra></extra>',
        text=vals,textposition='outside',cliponaxis=False))
    style(fig,height)
    fig.update_layout(xaxis_title=title,yaxis_title='')
    if len(df): fig.update_xaxes(range=[0,max(1,float(df[metric].max())*1.21)])
    return fig


def heatmap(df):
    # Data comes from the original BigQuery GROUP BY; weighted mean is required.
    grouped = df.groupby(['product_category','shipping_method'],observed=True,dropna=False)[['orders','returns']].sum().reset_index()
    grouped['rate'] = 100 * grouped.returns / grouped.orders
    matrix = grouped.pivot(index='product_category',columns='shipping_method',values='rate')
    labels = matrix.round(1).fillna(-1)
    fig = go.Figure(go.Heatmap(z=matrix.to_numpy(),x=matrix.columns,y=matrix.index,
        colorscale=[[0,'#E7F0FF'],[.5,'#7CB6F5'],[1,'#235B9F']],
        text=labels.to_numpy(),texttemplate='%{text:.1f}%',textfont={'size':12},
        hovertemplate='%{y} × %{x}<br>Return rate: %{z:.2f}%<extra></extra>',
        colorbar=dict(title='%',thickness=12)))
    style(fig,360)
    fig.update_layout(margin=dict(l=0,r=14,t=14,b=8),showlegend=False,xaxis_title='',yaxis_title='')
    return fig


def risk_histogram(df, threshold):
    fig=px.histogram(df,x='risk_score',nbins=38,opacity=.9,color_discrete_sequence=[TEAL])
    fig.add_vline(x=threshold,line_color=ORANGE,line_dash='dash',line_width=2,
        annotation_text=f'Ngưỡng thử {threshold:.2f}',annotation_position='top right')
    style(fig,370)
    fig.update_layout(xaxis_title='Điểm dự đoán (0–1)',yaxis_title='Số đơn',bargap=.08)
    return fig


def flagged_bars(train, columns, labels):
    # GROUP BY data contains counts of flags; never count groups as 1 order.
    pairs = sorted([
        (labels.get(col,col),int(train[col+'_count'].sum()))
        for col in columns if col+'_count' in train.columns
    ], key=lambda x:x[1])
    fig=go.Figure(go.Bar(y=[p[0] for p in pairs],x=[p[1] for p in pairs],orientation='h',marker_color=BLUE,
                          text=[f'{p[1]:,}' for p in pairs],textposition='outside',cliponaxis=False))
    style(fig,390); fig.update_layout(xaxis_title='Bản ghi được gắn cờ',yaxis_title='')
    upper=max([1]+[p[1] for p in pairs])*1.20
    fig.update_xaxes(range=[0,upper]);return fig


def confusion(data):
    values=data[['Predicted_Not_Returned','Predicted_Returned']].to_numpy()
    fig=go.Figure(go.Heatmap(z=values,x=['Dự đoán không hoàn','Dự đoán hoàn'],y=['Thực tế không hoàn','Thực tế hoàn'],
        colorscale=[[0,'#EEF4FF'],[1,'#286DC4']],showscale=False,
        text=values,texttemplate='%{text:,}',textfont=dict(size=20),
        hovertemplate='%{y}<br>%{x}: %{z:,}<extra></extra>'))
    style(fig,330)
    fig.update_layout(margin=dict(l=8,r=8,t=12,b=10),xaxis_title='',yaxis_title='')
    return fig
