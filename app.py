from flask import Flask,request,redirect,render_template,jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import re
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("DATABASE_URL =", os.environ.get("DATABASE_URL"))

db =SQLAlchemy(app)

class Players(db.Model):
    player_id = db.Column(db.String(50), primary_key=True)
    score = db.Column(db.Integer)
    average = db.Column(db.String(20))
    rank = db.Column(db.Integer)
    time = db.Column(db.String(50))

with app.app_context():
    db.create_all()

player_data = ''

expression_list = set()
operators = ['+','-','*','/']
def expression(maxi,lenght,level):
    mini=0
    global expression_list
    while True:
        nums=[str(random.randint(mini,maxi)) for _ in range(lenght)]
        while True:
            operands=''
            for i in range(level):
                if len(operands)>=3:
                    pass
                else:
                    operands+=nums[i]
                operands +=random.choice(operators)
                operands +=nums[i+1]
            if '/0' in operands:
                continue
            else:
                break
        if operands in expression_list and len(expression_list) < 390:
            continue
        else:
            if len(expression_list) != 390:
                expression_list.add(operands)
                break
            else:
                expression_list = set()
                break
    return operands

@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login/<player>')
def login(player):
    check_player = db.session.query(Players.player_id).all()
    player_list = [i[0] for i in check_player]
    if player in player_list:
        return render_template('main.html', player=player)
    else:
        player = 'Player id does not exists'
        return render_template('login.html', player=player)
    
@app.route('/new_login/<player>')
def new_login(player):
    check_player = db.session.query(Players.player_id).all()
    player_list = [i[0] for i in check_player]
    if player in player_list:
        player = 'Player id already exists try another'
        return render_template('login.html', new_player=player)
    else:
        player_data = Players(
            player_id = player
        )
        db.session.add(player_data)
        db.session.commit()
    return render_template('main.html', player=player)

@app.route('/level/<player>')
def level(player):
    return render_template('choose_level.html', player=player)

@app.route('/game/<level>/<player>')
def start_game(level,player):
    exp = ""
    if level == 'Easy':
        exp = expression(9,2,1)
        exp = '(' +exp+ ')'
        exp = ' '.join(exp)
    elif level == 'Medium':
        exp = expression(20,3,2)
        exp = '( ' +exp+ ' )'
    else:
        exp = expression(30,4,3)
        exp = '( ' +exp+ ' )'
    return render_template('game.html', 
                           level=level,
                           exp=exp,
                           player=player
                           )

@app.route('/update', methods=['GET','POST'])
def update():
    game_data = request.get_json()
    count = int(game_data['count'])
    score = int(game_data['score'])
    answer = game_data['answer'].strip()
    level = game_data['level']
    exp = game_data['exp']
    new_exp = ""
    status = ''
    if level == 'Easy':
        old_exp = expression(9,2,1)
        new_exp = '(' +old_exp+ ')'
        new_exp = ' '.join(new_exp)
    elif level == 'Medium':
        old_exp = expression(20,3,2)
        new_exp = '( ' +old_exp+ ' )'
    else:
        old_exp = expression(30,4,3)
        new_exp = '( ' +old_exp+ ' )'
    exp = re.sub(r'[^0-9+\-*/().]', '', exp)
    result = eval(exp)
    if '.' not in str(result):
        if str(result) == answer:
            status = 'Correct'
            new_count = count+1
            new_score = score+5
        else:
            status = f'Incorrect. The Answer is: {result}'
            new_count = count+1
            new_score = score
    else:
        if float(answer) == round(float(result),2):
            status = 'Correct'
            new_count = count+1
            new_score = score+5
        else:
            status = f'Incorrect. The Answer is: {round(float(result),2)}'
            new_count = count+1
            new_score = score
    return jsonify({
        'new_count':new_count,
        'new_score':new_score,
        'new_exp':new_exp,
        'status':status
    })

@app.route('/back/<player>')
def go_back(player):
    return render_template('main.html', player=player)

@app.route('/score_card', methods=['GET','POST'])
def score_card():
    score_card = request.get_json()
    score = int(score_card['score'])
    count = int(score_card['count'])
    level = score_card['level']
    time = score_card['time']
    player = score_card['player']
    average =''

    if score ==0:
        average = '0%'
    else:
        average = str(round(score/count*20,2))+'%'
    values = Players.query.get(player)
    if values.score:
        if score >= values.score:
            values.score = score
            values.average = average
            values.time = time
            db.session.commit()
    else:
        values.score = score
        values.average = average
        values.time = time
        db.session.commit()
    return render_template('score_card.html', 
                           final_score=score,
                           final_count=count,
                           final_level=level,
                           final_time=time,
                           final_average=average,
                           player=player
                           )

@app.route('/leaderboard')
def leader_board():
    players = Players.query.order_by(Players.score.desc()).all()

    rank = 1

    for player in players:
        player.rank = rank
        rank += 1

    db.session.commit()
    return render_template('leader_board.html', leader_board=players)

@app.route('/back_to_scorecard')
def back_to_scorecard():
    return redirect('/score_card')

if __name__ == '__main__':
    app.run(debug=True)