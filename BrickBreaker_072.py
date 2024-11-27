import tkinter as tk

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y, speed_multiplier=1):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 5 * speed_multiplier
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y, width_multiplier=1):
        self.width = 80 * width_multiplier
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {
        3: '#00FF00',  # Lime for 3-hit bricks
        2: '#87CEEB',  # Sky Blue for 2-hit bricks
        1: '#FF6B6B'   # Bright Red for 1-hit bricks
    }

    def __init__(self, canvas, x, y, hits):
        self.width = 100
        self.height = 30
        self.hits = hits
        color = self.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=self.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.master = master
        self.difficulty = None
        self.score = 0
        self.lives = 3
        self.width = 800
        self.height = 580
        self.is_paused = False
        self.game_started = False  # Flag to track game start
        self.is_resetting = False  # New flag to prevent pause during reset
        
        self.canvas = tk.Canvas(self, bg='#C0C0C0', width=self.width, height=self.height,)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.show_difficulty_selection()

    def show_difficulty_selection(self):
        self.canvas.delete('all')
        self.draw_text(400, 150, 'Select Difficulty', size='30')
        
        difficulties = [
            ('Easy', 1.0, 1.0),
            ('Medium', 0.75, 1.5),
            ('Hard', 0.5, 2.0)
        ]
        
        for i, (name, paddle_width, ball_speed) in enumerate(difficulties):
            y_pos = 250 + i * 70
            self.canvas.create_rectangle(250, y_pos, 550, y_pos + 50, fill='#FFB643', tags=f'{name.lower()}_difficulty')
            self.canvas.create_text(400, y_pos + 25, text=name, font=('Comic Sans MS', 17), tags=f'{name.lower()}_difficulty')
            self.canvas.tag_bind(f'{name.lower()}_difficulty', '<Button-1>', 
                                  lambda e, d=name, pw=paddle_width, bs=ball_speed: 
                                  self.start_game_with_difficulty(d, pw, bs))

    def start_game_with_difficulty(self, difficulty, paddle_width, ball_speed):
        self.difficulty = difficulty
        self.ball_speed_multiplier = ball_speed
        self.paddle_width_multiplier = paddle_width
        
        self.canvas.delete('all')
        
        self.paddle = Paddle(self.canvas, self.width/2, 450, paddle_width)
        self.items[self.paddle.item] = self.paddle
        
        brick_width = 100 
        brick_height = 30
        padding = 4
        start_x = (self.width - (7 * (brick_width + padding))) / 2
        
        for row, hits in enumerate([3, 2, 1]):  
            for col in range(7):  
                x = start_x + col * (brick_width + padding)  
                y = 100 + row * (brick_height + padding)  
                self.add_brick(x + brick_width/2, y, hits)

        self.score = 0
        self.hud = None
        self.is_paused = False
        self.game_started = False
        self.is_resetting = False  # Reset resetting flag
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.move(-15) if not self.is_paused else None)
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.move(15) if not self.is_paused else None)
        # Add pause key binding
        self.canvas.bind('p', self.toggle_pause)

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 430, self.ball_speed_multiplier)
        self.paddle.set_ball(self.ball)

    def setup_game(self):
        self.is_resetting = True  # Set resetting flag
        self.add_ball()
        self.update_lives_text()
        self.update_score_text()
        
        # Add pause explanation text
        self.pause_explanation = self.draw_text(400, 500, 'Press "P" to Pause/Unpause the Game', '15')
        
        self.text = self.draw_text(400, 300, 'Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Comic Sans MS', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(100, 30, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def update_score_text(self):
        text = 'Score: %s' % self.score
        if hasattr(self, 'score_text'):
            self.canvas.itemconfig(self.score_text, text=text)
        else:
            self.score_text = self.draw_text(700, 30, text, 15)

    def toggle_pause(self, event=None):
        # Only allow pausing if the game has started and is not resetting
        if not self.game_started or self.is_resetting:
            return

        self.is_paused = not self.is_paused
        if self.is_paused:
            # Display pause text
            self.pause_text = self.draw_text(400, 300, 'PAUSED', '50')
            # Add additional pause explanation
            self.pause_explanation_detail = self.draw_text(400, 370, 'Press "P" to continue', '20')
        else:
            # Remove pause text and continue game loop
            if hasattr(self, 'pause_text'):
                self.canvas.delete(self.pause_text)
            if hasattr(self, 'pause_explanation_detail'):
                self.canvas.delete(self.pause_explanation_detail)
            self.game_loop()

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        # Remove pause explanation text when game starts
        if hasattr(self, 'pause_explanation'):
            self.canvas.delete(self.pause_explanation)
        self.paddle.ball = None
        self.game_started = True
        self.is_resetting = False  # Unset resetting flag
        self.game_loop()

    def game_loop(self):
        # Check if game is paused
        if self.is_paused:
            return

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0: 
            self.ball.speed = None
            self.game_started = False  # Reset game started flag
            # Clear canvas and show you win text
            self.canvas.delete('all')  
            self.draw_text(400, 200, 'You Win!')  
            self.draw_text(400, 250, f'Difficulty: {self.difficulty}')  
            self.draw_text(400, 300, f'Score: {self.score}')  
        
            # Add a "Return to Home" button  
            return_btn = self.canvas.create_rectangle(  
                325, 350, 475, 400,   
                fill='#FFB643', tags='return_home'  
            )  
            return_btn_text = self.canvas.create_text(  
                400, 375,   
                text='Return Home',   
                font=('Comic Sans MS', 14),  
                tags='return_home'  
            )  
        
            # Bind click event to return to difficulty selection  
            self.canvas.tag_bind('return_home', '<Button-1>',   
                                lambda e: self.show_difficulty_selection())
        elif self.ball.get_position()[3] >= self.height: 
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.game_started = False  # Reset game started flag
                # Clear canvas and show game over text
                self.canvas.delete('all')
                self.draw_text(400, 200, 'Game Over!')
                self.draw_text(400, 250, f'Score: {self.score}')
                
                # Add a "Return to Home" button
                return_btn = self.canvas.create_rectangle(
                    325, 300, 475, 350, 
                    fill='#FFB643', tags='return_home'
                )
                return_btn_text = self.canvas.create_text(
                    400, 325, 
                    text='Return Home', 
                    font=('Comic Sans MS', 14),
                    tags='return_home'
                )
                
                # Bind click event to return to difficulty selection
                self.canvas.tag_bind('return_home', '<Button-1>', 
                                     lambda e: self.show_difficulty_selection())
            else:
                self.is_resetting = True  # Set resetting flag
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        
        for obj in objects:
            if isinstance(obj, Brick):
                self.score += 10  # Add points for each brick hit
                self.update_score_text()
        
        self.ball.collide(objects)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    root.mainloop()