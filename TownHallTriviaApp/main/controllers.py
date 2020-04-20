from flask import Blueprint, render_template, session, url_for, redirect, request
import redisCacheManager
import flaskSessionManager

main = Blueprint("main", __name__, template_folder="templates")
redisManager = redisCacheManager.RedisClass()
sessionManager = flaskSessionManager.FlaskSessionManager()

@main.route('/')
def index():
    return render_template('main/index.html')

@main.route('/validateGameId', methods = ["POST"])
def validateGameId():
    if redisManager.doesGameExist(request.form["gameId"]):
        sessionManager.setPlayerGameId(request.form["gameId"])
        if redisManager.isGameEnabled(request.form["gameId"]):
            sessionManager.setMessage("Let's get ready to rumble!")
            return redirect(url_for("main.registerTeam"))
        else:
            sessionManager.setMessage("")
            return redirect(url_for("main.gameWaitingRoom"))
    else:
        sessionManager.setMessage("Your Game Id isn't valid")
        return redirect(url_for("main.error", gameId=request.form["gameId"]))

@main.route('/gameWaitingRoom')
def gameWaitingRoom():
    if redisManager.isGameEnabled(sessionManager.getPlayerGameId()):
        sessionManager.setMessage("Thanks for your patience. Now let's get your team registered!")
        return redirect(url_for("main.registerTeam"))
    else:
        return render_template("main/gameWaitingRoom.html", gameId=sessionManager.getPlayerGameId(), message=sessionManager.getMessage())

@main.route('/registerTeam')
def registerTeam():
    if redisManager.isGameEnabled(sessionManager.getPlayerGameId()):
        return render_template("main/registerTeam.html", gameId=sessionManager.getPlayerGameId(), message=sessionManager.getMessage())
    else:
        sessionManager.setMessage("")
        return render_template("main/gameWaitingRoom.html", gameId=sessionManager.getPlayerGameId())

@main.route('/error')
def error():
    return render_template("main/error.html", gameId=request.args.get('gameId'), message=sessionManager.getMessage())

@main.route('/teamRegisterSuccess', methods = ["POST"])
def teamRegisterSuccess():
    if request.method == "POST":
        if sessionManager.isTeamRegistered():
            sessionManager.unregisterTeam()
        if not redisManager.addTeamToGame(sessionManager.getPlayerGameId(), request.form["teamName"]):
            # Team name has been taken and they need to re-register
            sessionManager.setMessage("WHOOPS, Team Name Taken! The team name \"" + request.form["teamName"] + "\" has already been selected by another team, guess you gotta sign up earlier next time.")
            return redirect(url_for("main.registerTeam"))
        else:
            sessionManager.setTeamName(request.form["teamName"])
            sessionManager.setMessage("Succesfull registration!")
            return redirect(url_for("main.confirmation"))

@main.route('/confirmation')
def confirmation():
    return render_template("main/confirmation.html", gameId=sessionManager.getPlayerGameId(), teamName=sessionManager.getTeamName(), message=sessionManager.getMessage())

@main.route('/gamePlayRoom')
def gamePlayRoom():
    return render_template("main/gamePlayRoom.html", gameId=sessionManager.getPlayerGameId(), teamName=sessionManager.getTeamName())

@main.route('/playRound', methods = ["POST"])
def playRound():
    if request.method == "POST":
        if not redisManager.isGameEnabled(sessionManager.getPlayerGameId()):
            sessionManager.setMessage("Trivia Game \"" + sessionManager.getPlayerGameId() + "\" is no longer Enabled")
            return redirect(url_for("main.gameWaitingRoom"))
        sessionManager.setRoundId(request.form["roundId"])
        if redisManager.isRoundEnabled(sessionManager.getPlayerGameId(), sessionManager.getRoundId()):
            return render_template("main/round.html", teamName=sessionManager.getTeamName(), roundId=sessionManager.getRoundId())
        return redirect(url_for("main.gamePlayRoom"))

@main.route('/submitTeamAnswers', methods = ["POST"])
def submitTeamAnswers():
    if request.method == "POST":
        if redisManager.isRoundEnabled(sessionManager.getPlayerGameId(), sessionManager.getRoundId()):
            redisManager.submitTeamAnswers(sessionManager.getPlayerGameId(), sessionManager.getTeamName(), sessionManager.getRoundId(), request.form)
            sessionManager.setMessage(sessionManager.getRoundId() + " Answer Submission Confirmation")
            return redirect(url_for("main.confirmation"))
        else:
            redisManager.submitTeamAnswers(sessionManager.getPlayerGameId(), sessionManager.getTeamName(), sessionManager.getRoundId(), {})
            sessionManager.setMessage("You unfortunately were not able to submit your form in time for " + sessionManager.getRoundId() + ". Try to submit earlier for the next round!")
            return redirect(url_for("main.confirmation"))

@main.route('/endGame')
def endGame():
    sessionManager.unregisterTeam()
    return render_template("main/endGame.html")
