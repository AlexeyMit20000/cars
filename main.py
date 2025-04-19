import math
import sys
import neat
import pygame

#размер трека в пикселях
WIDTH = 924
HEIGHT = 628

CAR_SIZE_X = 60    
CAR_SIZE_Y = 60

BORDER_COLOR = (255, 255, 255, 255) # цвет границы
current_generation = 0 # Счетчик поколений

class Car:

    def __init__(self):
        # Загрузка спрайта машины и его поворот
        self.sprite = pygame.image.load('car.png').convert() # Конвертация для ускорения
        self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
        self.rotated_sprite = self.sprite 
        self.position = [394, 540] # Начальная позиция машины
        self.angle = 0
        self.speed = 0
        self.speed_set = False # Флаг для установки скорости по умолчанию
        self.center = [self.position[0] + CAR_SIZE_X / 2, self.position[1] + CAR_SIZE_Y / 2] # Вычисление центра
        self.radars = [] # Список для сенсоров / радаров
        self.drawing_radars = [] # Радар для отрисовки
        self.alive = True # Булевый флаг для проверки, не разбилась ли машина
        self.distance = 0 # Пройденное расстояние
        self.time = 0 # Прошедшее время

    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.position) # Отрисовка спрайта
        self.draw_radar(screen) 

    def draw_radar(self, screen):
        # Опционально отрисовать все сенсоры / радары
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(screen, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(screen, (0, 255, 0), position, 5)

    def check_collision(self, game_map):
        self.alive = True
        for point in self.corners:
            # Если любая из углов касается цвета границы -> авария
            # Предполагается прямоугольник
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break

    def check_radar(self, degree, game_map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Пока не столкнемся с BORDER_COLOR И длина < 300 (максимум) -> идем дальше
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 300:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Вычисляем расстояние до границы и добавляем в список радаров
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])
    
    def update(self, game_map):
        # Установить скорость 20 в первый раз
        # Только при наличии 4 выходных узлов со скоростью вверх и вниз
        if not self.speed_set:
            self.speed = 20
            self.speed_set = True

        # Получить повернутый спрайт и двигаться в правильном направлении по X
        # Не позволять машине приближаться к краю менее чем на 20px
        self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        # Увеличить расстояние и время
        self.distance += self.speed
        self.time += 1
        
        # То же самое для Y-позиции
        self.position[1 ] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], HEIGHT - 120)

        # Вычислить новый центр
        self.center = [int(self.position[0]) + CAR_SIZE_X / 2, int(self.position[1]) + CAR_SIZE_Y / 2]

        # Вычислить четыре угла
        # Длина равна половине стороны
        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        # Проверка на столкновения и очистка радаров
        self.check_collision(game_map)
        self.radars.clear()

        # От -90 до 120 с шагом 45 проверяем радар
        for d in range(-90, 120, 45):
            self.check_radar(d, game_map)

    def get_data(self):
        # Получить расстояния до границы
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values

    def is_alive(self):
        # Базовая функция проверки живости
        return self.alive

    def get_reward(self):
        # Вычислить награду (возможно, изменить?)
        return self.distance / (CAR_SIZE_X / 2)

    def rotate_center(self, image, angle):
        # Повернуть прямоугольник
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image


def run_simulation(genomes, config):
    
    # Пустые коллекции для сетей и машин
    nets = []
    cars = []

    # Инициализация PyGame и дисплея
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    # Для всех переданных геномов создаем новую нейронную сеть
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(Car())

    # Настройки часов
    # Настройки шрифтов и загрузка карты
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Arial", 30)
    alive_font = pygame.font.SysFont("Arial", 20)
    game_map = pygame.image.load('map.png').convert() # Конвертация для ускорения

    global current_generation
    current_generation += 1

    # Простой счетчик для грубого ограничения времени (не лучший подход)
    counter = 0

    while True:
        # Выход при событии Quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # Для каждой машины получаем действие, которое она выполняет
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.angle += 10 # Влево
            elif choice == 1:
                car.angle -= 10 # Вправо
            elif choice == 2:
                if(car.speed - 2 >= 12):
                    car.speed -= 2 # Замедление
            else:
                car.speed += 2 # Ускорение
        
        # Проверка, жива ли ли машина
        still_alive = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                still_alive += 1
                car.update(game_map)
                genomes[i][1].fitness += car.get_reward()

        if still_alive == 0:
            break

        counter += 1
        if counter == 30 * 40: # Остановить примерно через 20 секунд
            break

        # Отрисовка карты и всех живых машин
        screen.blit(game_map, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(screen)
        
        # Отображение информации
        text = generation_font.render("Поколение: " + str(current_generation), True, (0,0,0))
        text_rect = text.get_rect()
        text_rect.center = (400, 200)
        screen.blit(text, text_rect)

        text = alive_font.render("Еще в строю: " + str(still_alive), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (400, 230)
        screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    
    # Загрузка конфигурации
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # Создание популяции и добавление репортеров
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    # Запуск симуляции на максимум 100 поколений
    population.run(run_simulation, 100)