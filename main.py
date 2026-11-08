import math
import random
from dataclasses import dataclass, field

import pygame


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 760
PANEL_TOP = 600
EARTH_RADIUS_M = 6_371_000.0
EARTH_MU = 3.986004418e14
# Height of the cannon above Earth's surface, in meters.
CANNON_ALTITUDE_M = 300_000.0
EARTH_CENTER = (WINDOW_WIDTH // 2, 330)
EARTH_RADIUS_PX = 170
METERS_PER_PIXEL = EARTH_RADIUS_M / EARTH_RADIUS_PX
PHYSICS_STEP_S = 0.05
SIMULATION_SPEED = 600.0
MAX_TRAIL_POINTS = 4000

BACKGROUND = (5, 10, 25)
TEXT = (230, 238, 250)
MUTED_TEXT = (160, 177, 200)
ACCENT = (100, 205, 255)
PANEL = (15, 25, 45)


@dataclass
class Simulation:
    position: list[float] = field(default_factory=list)
    velocity: list[float] = field(default_factory=list)
    trail: list[tuple[int, int]] = field(default_factory=list)
    elapsed_s: float = 0.0
    running: bool = False
    paused: bool = False
    impacted: bool = False
    draw_trail: bool = True

    @property
    def distance_m(self) -> float:
        return math.hypot(*self.position)

    @property
    def speed_m_s(self) -> float:
        return math.hypot(*self.velocity)


def gravity_acceleration(position: list[float]) -> list[float]:
    distance = math.hypot(*position)
    if distance == 0:
        return [0.0, 0.0]
    factor = -EARTH_MU / distance**3
    return [factor * position[0], factor * position[1]]


def world_to_screen(position: list[float]) -> tuple[int, int]:
    return (
        round(EARTH_CENTER[0] + position[0] / METERS_PER_PIXEL),
        round(EARTH_CENTER[1] + position[1] / METERS_PER_PIXEL),
    )


def format_number(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def start_simulation(acceleration: float, duration: float) -> Simulation:
    return Simulation(
        position=[0.0, -(EARTH_RADIUS_M + CANNON_ALTITUDE_M)],
        velocity=[acceleration * duration, 0.0],
        running=True,
    )


def advance_simulation(simulation: Simulation, seconds: float) -> None:
    remaining = seconds
    while remaining > 1e-9 and simulation.running and not simulation.paused:
        step = min(PHYSICS_STEP_S, remaining)
        acceleration_start = gravity_acceleration(simulation.position)
        next_position = [
            simulation.position[index]
            + simulation.velocity[index] * step
            + 0.5 * acceleration_start[index] * step**2
            for index in range(2)
        ]
        acceleration_end = gravity_acceleration(next_position)
        simulation.velocity = [
            simulation.velocity[index]
            + 0.5 * (acceleration_start[index] + acceleration_end[index]) * step
            for index in range(2)
        ]
        simulation.position = next_position
        simulation.elapsed_s += step
        remaining -= step

        if simulation.distance_m < EARTH_RADIUS_M - 0.5:
            simulation.impacted = True
            simulation.running = False


def trajectory_category(simulation: Simulation) -> str:
    distance = simulation.distance_m
    speed_squared = simulation.velocity[0] ** 2 + simulation.velocity[1] ** 2
    specific_energy = speed_squared / 2 - EARTH_MU / distance
    if specific_energy >= -(EARTH_MU / distance) * 1e-10:
        return "Velocidade de escape atingida"

    angular_momentum = (
        simulation.position[0] * simulation.velocity[1]
        - simulation.position[1] * simulation.velocity[0]
    )
    eccentricity = math.sqrt(
        max(0.0, 1 + 2 * specific_energy * angular_momentum**2 / EARTH_MU**2)
    )
    semi_major_axis = -EARTH_MU / (2 * specific_energy)
    periapsis = semi_major_axis * (1 - eccentricity)
    if periapsis < EARTH_RADIUS_M - 0.5:
        return "Trajetoria suborbital"
    if eccentricity <= 0.01:
        return "Orbita quase circular"
    return "Orbita eliptica"


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int] = TEXT,
) -> None:
    surface.blit(font.render(text, True, color), position)


def draw_earth(surface: pygame.Surface) -> None:
    center = EARTH_CENTER
    radius = EARTH_RADIUS_PX
    pygame.draw.circle(surface, (28, 99, 176), center, radius)
    pygame.draw.circle(surface, (61, 151, 221), center, radius, 2)

    clip = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    previous_clip = surface.get_clip()
    surface.set_clip(clip)
    continents = [
        [(420, 286), (438, 268), (462, 274), (470, 294), (455, 308), (449, 332), (430, 323)],
        [(468, 341), (487, 350), (492, 374), (480, 397), (475, 423), (462, 407), (459, 379)],
        [(506, 281), (530, 267), (553, 279), (546, 298), (527, 304), (520, 325), (501, 311)],
        [(534, 327), (557, 320), (580, 335), (568, 349), (549, 346)],
        [(534, 388), (557, 379), (581, 394), (573, 414), (552, 421), (536, 408)],
    ]
    for points in continents:
        pygame.draw.polygon(surface, (57, 159, 119), points)
    
    surface.set_clip(previous_clip)

    surface.set_clip(None)
    pygame.draw.circle(surface, (111, 190, 245), center, radius, 2)


def draw_cannon(surface: pygame.Surface) -> None:
    altitude_px = CANNON_ALTITUDE_M / METERS_PER_PIXEL
    top = (
        EARTH_CENTER[0],
        round(EARTH_CENTER[1] - EARTH_RADIUS_PX - altitude_px),
    )
    pygame.draw.line(surface, (228, 233, 241), top, (top[0] + 32, top[1]), 9)
    pygame.draw.circle(surface, (194, 205, 221), top, 11)
    pygame.draw.circle(surface, (92, 104, 122), (top[0] + 30, top[1]), 5)


def draw_controls(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    acceleration_text: str,
    duration_text: str,
    focused_field: str | None,
    message: str,
    simulation: Simulation,
    simulation_speed: float,
) -> None:
    pygame.draw.rect(surface, PANEL, (0, PANEL_TOP, WINDOW_WIDTH, WINDOW_HEIGHT - PANEL_TOP))
    pygame.draw.line(surface, (44, 66, 98), (0, PANEL_TOP), (WINDOW_WIDTH, PANEL_TOP), 2)

    draw_text(surface, fonts["small"], "Aceleracao do canhao (m/s2)", (28, 621), MUTED_TEXT)
    draw_text(surface, fonts["small"], "Duracao do disparo (s)", (300, 621), MUTED_TEXT)
    acceleration_box = pygame.Rect(28, 645, 220, 42)
    duration_box = pygame.Rect(300, 645, 220, 42)
    for rect, field_name in ((acceleration_box, "acceleration"), (duration_box, "duration")):
        color = ACCENT if focused_field == field_name else (61, 83, 117)
        pygame.draw.rect(surface, (8, 15, 29), rect, border_radius=6)
        pygame.draw.rect(surface, color, rect, 2, border_radius=6)
    draw_text(surface, fonts["body"], acceleration_text, (acceleration_box.x + 10, acceleration_box.y + 8))
    draw_text(surface, fonts["body"], duration_text, (duration_box.x + 10, duration_box.y + 8))

    button_specs = [
        ("Disparar", pygame.Rect(558, 645, 125, 42), (25, 113, 162)),
        ("Reiniciar", pygame.Rect(696, 645, 125, 42), (52, 72, 103)),
        ("Pausar" if not simulation.paused else "Continuar", pygame.Rect(834, 645, 138, 42), (52, 72, 103)),
    ]
    for label, rect, color in button_specs:
        pygame.draw.rect(surface, color, rect, border_radius=6)
        draw_text(surface, fonts["small"], label, (rect.x + 15, rect.y + 12))

    draw_text(
        surface,
        fonts["small"],
        "Clique nos campos para editar | Enter aplica | Espaco dispara",
        (28, 701),
        MUTED_TEXT,
    )
    draw_text(
        surface,
        fonts["small"],
        "R reinicia | P pausa | +/- velocidade | T rastro",
        (28, 731),
        MUTED_TEXT,
    )

    draw_text(surface, fonts["small"], message, (28, 731), (255, 195, 115) if message else MUTED_TEXT)
    draw_text(surface, fonts["small"], f"Tempo simulado: {format_number(simulation.elapsed_s, 1)} s", (588, 701), MUTED_TEXT)
    draw_text(surface, fonts["small"], f"Velocidade da simulacao: {simulation_speed:.0f}x", (588, 731), MUTED_TEXT)


def parse_positive_value(text: str, label: str) -> float:
    try:
        value = float(text.strip().replace(",", "."))
    except ValueError as error:
        raise ValueError(f"Valor invalido para {label}. Digite um numero positivo.") from error
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} deve ser um numero finito maior que zero.")
    return value


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("O Canhao de Newton - simulador de gravidade")
    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.Font(None, 34),
        "body": pygame.font.Font(None, 28),
        "small": pygame.font.Font(None, 22),
    }

    random.seed(7)
    stars = [
        (random.randrange(WINDOW_WIDTH), random.randrange(PANEL_TOP), random.choice((1, 1, 2)))
        for _ in range(110)
    ]
    acceleration_text = "10000"
    duration_text = "0,77299"
    focused_field: str | None = None
    message = ""
    simulation_speed = SIMULATION_SPEED
    simulation = Simulation()
    running = True

    while running:
        frame_seconds = min(clock.tick(60) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse = event.pos
                if pygame.Rect(28, 645, 220, 42).collidepoint(mouse):
                    focused_field = "acceleration"
                    acceleration_text = ""
                elif pygame.Rect(300, 645, 220, 42).collidepoint(mouse):
                    focused_field = "duration"
                    duration_text = ""
                elif pygame.Rect(558, 645, 125, 42).collidepoint(mouse):
                    focused_field = None
                    try:
                        acceleration = parse_positive_value(acceleration_text, "A aceleracao")
                        duration = parse_positive_value(duration_text, "A duracao")
                        simulation = start_simulation(acceleration, duration)
                        message = ""
                    except ValueError as error:
                        message = str(error)
                elif pygame.Rect(696, 645, 125, 42).collidepoint(mouse):
                    simulation = Simulation()
                    message = ""
                elif pygame.Rect(834, 645, 138, 42).collidepoint(mouse) and simulation.running:
                    simulation.paused = not simulation.paused
                else:
                    focused_field = None
            elif event.type == pygame.TEXTINPUT and focused_field is not None:
                accepted = "".join(character for character in event.text if character in "0123456789.,")
                if focused_field == "acceleration":
                    acceleration_text += accepted
                else:
                    duration_text += accepted
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    focused_field = None
                elif event.key == pygame.K_RETURN and focused_field is not None:
                    try:
                        current_text = acceleration_text if focused_field == "acceleration" else duration_text
                        label = "A aceleracao" if focused_field == "acceleration" else "A duracao"
                        parse_positive_value(current_text, label)
                        message = f"{label} atualizada."
                    except ValueError as error:
                        message = str(error)
                    focused_field = None
                elif focused_field is not None and event.key == pygame.K_BACKSPACE:
                    if focused_field == "acceleration":
                        acceleration_text = acceleration_text[:-1]
                    else:
                        duration_text = duration_text[:-1]
                elif focused_field is None:
                    if event.key == pygame.K_SPACE:
                        try:
                            acceleration = parse_positive_value(acceleration_text, "A aceleracao")
                            duration = parse_positive_value(duration_text, "A duracao")
                            simulation = start_simulation(acceleration, duration)
                            message = ""
                        except ValueError as error:
                            message = str(error)
                    elif event.key == pygame.K_r:
                        simulation = Simulation()
                        message = ""
                    elif event.key == pygame.K_p and simulation.running:
                        simulation.paused = not simulation.paused
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        simulation_speed *= 2
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        simulation_speed = max(1.0, simulation_speed / 2)
                    elif event.key == pygame.K_t:
                        simulation.draw_trail = not simulation.draw_trail

        if simulation.running and not simulation.paused:
            advance_simulation(simulation, frame_seconds * simulation_speed)
            point = world_to_screen(simulation.position)
            if not simulation.trail or point != simulation.trail[-1]:
                simulation.trail.append(point)
                if len(simulation.trail) > MAX_TRAIL_POINTS:
                    del simulation.trail[: len(simulation.trail) - MAX_TRAIL_POINTS]

        screen.fill(BACKGROUND)
        for x, y, radius in stars:
            pygame.draw.circle(screen, (112, 137, 170), (x, y), radius)

        draw_text(screen, fonts["title"], "O CANHAO DE NEWTON", (28, 22))
        draw_text(
            screen,
            fonts["small"],
            f"Raio da Terra: 6.371 km  |  Altitude do canhao: {format_number(CANNON_ALTITUDE_M / 1000)} km  |  Escala: 1 px = {METERS_PER_PIXEL:,.0f} m",
            (28, 59),
            MUTED_TEXT,
        )
        draw_earth(screen)

        if len(simulation.trail) > 1 and simulation.draw_trail:
            pygame.draw.lines(screen, (255, 204, 100), False, simulation.trail, 2)
        draw_cannon(screen)
        if simulation.running or simulation.impacted:
            ball_position = world_to_screen(simulation.position)
            if -20 <= ball_position[0] <= WINDOW_WIDTH + 20 and -20 <= ball_position[1] <= PANEL_TOP + 20:
                pygame.draw.circle(screen, (255, 220, 130), ball_position, 7)
                pygame.draw.circle(screen, (255, 248, 220), ball_position, 3)

        if simulation.running or simulation.impacted:
            altitude = max(0.0, simulation.distance_m - EARTH_RADIUS_M)
            info = (
                f"Velocidade: {format_number(simulation.speed_m_s)} m/s"
                f"  |  Altitude: {format_number(altitude / 1000, 1)} km"
                f"  |  g atual: {format_number(EARTH_MU / simulation.distance_m**2, 2)} m/s2"
            )
            draw_text(screen, fonts["small"], info, (28, 91), TEXT)
            category = "Impacto com a Terra" if simulation.impacted else trajectory_category(simulation)
            draw_text(screen, fonts["small"], category, (28, 117), ACCENT)
        else:
            cannon_distance = EARTH_RADIUS_M + CANNON_ALTITUDE_M
            orbital_speed = math.sqrt(EARTH_MU / cannon_distance)
            escape_speed = math.sqrt(2 * EARTH_MU / cannon_distance)
            try:
                launch_speed = parse_positive_value(
                    acceleration_text, "A aceleracao"
                ) * parse_positive_value(duration_text, "A duracao")
                launch_speed_label = f"Velocidade inicial calculada: {format_number(launch_speed)} m/s"
            except ValueError:
                launch_speed_label = "Informe aceleracao e duracao positivas para calcular a velocidade."
            draw_text(
                screen,
                fonts["small"],
                launch_speed_label,
                (28, 91),
                TEXT,
            )
            draw_text(
                screen,
                fonts["small"],
                f"Na altura do canhao: orbital {format_number(orbital_speed)} m/s  |  escape {format_number(escape_speed)} m/s",
                (28, 117),
                MUTED_TEXT,
            )

        draw_controls(
            screen,
            fonts,
            acceleration_text,
            duration_text,
            focused_field,
            message,
            simulation,
            simulation_speed,
        )
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
