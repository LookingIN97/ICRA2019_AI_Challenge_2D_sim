#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018 Chenrui Lei
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import math
import json
from copy import deepcopy
from map import Map
from game_objects import GameObject, Wall, Robot, Zone, Polygon, Circle
from physics import Vector2D, Vector3D, Orient2D, Pose2D, Velocity2D, Acceleration2D
from collision_engine_2d import CollisionEngine2D, LineSegment2D, Point2D, Line2D

class Game:
    """The game backgound core"""

    def __init__(self, config_path):
        """Game constructor.

        Args:
            config_path (:obj:`str`): The path to the game config JSON file.

        """
        self.game_objects = []

        # Load json format map configration
        with open(config_path, 'r') as f:
            map_config = json.load(f)

        # Load map properties
        self.map = Map(
            width=map_config['config']['map_width'],
            height=map_config['config']['map_height'],
            wall_thickness=map_config['config']['wall_thickness']
        )

        # Create zones
        for zone in map_config['config']['zones']:
            self.add_game_object(
                Zone(
                    Pose2D(
                        position=Vector2D(
                            zone['coords']['x'],
                            zone['coords']['y'],
                        ),
                        orientation=Orient2D(math.radians(zone['orientation']))
                    ),
                    map_config['config']['zone_side_length'],
                    zone['id']
                )
            )

        # Create walls
        for wall in map_config['config']['walls']:
            self.add_game_object(
                Wall(
                    Pose2D(
                        position=Vector2D(wall['coords']['x'], wall['coords']['y']),
                        orientation=Orient2D(math.radians(wall['orientation']))
                    ),
                    wall['length'],
                    map_config['config']['wall_thickness']
                )
            )

        # Create robots
        for robot in map_config['config']['robots']:
            self.add_game_object(
                Robot(
                    Pose2D(
                        position=Vector2D(
                            robot['coords']['x'],
                            robot['coords']['y']
                        ),
                        orientation=Orient2D(math.radians(robot['orientation']))
                    ),
                    robot['length'], robot['width'],
                    robot['robot_id']
                )
            )


    def add_game_object(self, obj):
        if not isinstance(obj, GameObject):
            raise TypeError(
                "Cannot add '{:}' type as a game object.".format(
                    type(obj).__name__
                )
            )
        self.game_objects.append(obj)


    def update(self, t_interval):
        """The game update logic."""
        # Update game objects
        for game_obj in self.game_objects:
            old_pose = deepcopy(game_obj.pose)
            game_obj.update(t_interval)

            if type(game_obj) is Robot: #or type(game_obj) is Bullet:
                # Collision check
                # TODO:
                collision = False

                for another_obj in self.game_objects:
                    if type(another_obj) is Robot and \
                    game_obj is not another_obj and \
                    game_obj.pose.position.find_distance(
                        another_obj.pose.position
                    ) < game_obj.radius + another_obj.radius:
                        # Collision with other robots
                        # game_obj.moveTo(old_pose)
                        collision = True
                        break



                    if type(another_obj) is Wall:
                        vertex = deepcopy(another_obj.shape_set[0].vertex)
                        coords = []
                        for v in vertex:
                            if collision:
                                break
                            new_v = v.rotate(
                                another_obj.pose.orientation.z
                            )
                            new_v += another_obj.pose.position

                            if new_v.find_distance(
                                game_obj.pose.position
                            ) < game_obj.radius:
                                # Collision with a wall corner
                                collision = True
                                break

                            coords.append(new_v)

                        edges = []
                        for i in range(len(coords)):
                            if collision:
                                break
                            new_line = LineSegment2D(
                                Point2D(coords[i].x, coords[i].y),
                                Point2D(coords[(i+1)%len(coords)].x, coords[(i+1)%len(coords)].y)
                            )
                            edges.append(new_line)

                        for edge in edges:
                            if collision:
                                break
                            perpendicular_line = edge.find_perpendicular(through_point=Point2D(
                                game_obj.pose.position.x,
                                game_obj.pose.position.y
                            ))

                            intersetion = perpendicular_line.find_intersection(edge)

                            if intersetion!=False:
                                xmax = max(edge.point1.x, edge.point2.x)
                                xmin = min(edge.point1.x, edge.point2.x)
                                ymax = max(edge.point1.y, edge.point2.y)
                                ymin = min(edge.point1.y, edge.point2.y)

                                if (intersetion.x <= xmax or \
                                math.isclose(intersetion.x, xmax, rel_tol=1e-4)) \
                                and (intersetion.x >= xmin or \
                                math.isclose(intersetion.x, xmin, rel_tol=1e-4)) \
                                and (intersetion.y <= ymax or \
                                math.isclose(intersetion.y, ymax, rel_tol=1e-4)) \
                                and (intersetion.y >= ymin or \
                                math.isclose(intersetion.y, ymin, rel_tol=1e-4)) :

                                    if edge.find_distance(
                                        Point2D(
                                            game_obj.pose.position.x,
                                            game_obj.pose.position.y
                                        )
                                    ) < game_obj.radius:

                                        # Collision with a wall edge
                                        collision = True
                                        break

                if collision:
                    game_obj.moveTo(old_pose)



    def run(self):
        update_time_interval = 1#0.01
        while True:
            self.update(update_time_interval)
            time.sleep(update_time_interval)
            # print('game is running')
            print()


if __name__ == '__main__':
    # print(
    #     Pose2D(
    #         position=Vector2D(4000, 2500),
    #         orientation=Orient2D(0)
    #     ) == Pose2D(
    #         position=Vector2D(4000, 2500),
    #         orientation=Orient2D(0)
    #     )
    # )
    #
    # print(
    #     Vector2D(0, 0) == Vector3D(0, 0, 0)
    # )
    #
    # print(
    #     Vector3D(0, 0, 0) == Vector3D(0, 0, 0)
    # )
    #
    # print(
    #     Pose2D(
    #         position=Vector2D(4000, 2500),
    #         orientation=Orient2D(0)
    #     )
    # )
    #
    # print(
    #     repr(Vector2D(0, 0))
    # )
    #
    # print(
    #     repr(Vector3D(0, 0, 0))
    # )

    # print(
    #     Vector3D(0, 0, 0) + Vector2D(10, 15)
    # )

    # print(
    #     # type(
    #         -(Pose2D(
    #             position=Vector2D(4000, 2500),
    #             orientation=Orient2D(0)
    #         ) - Pose2D(
    #             position=Vector2D(4000, 2500),
    #             orientation=Orient2D(math.pi)
    #         ))
    #     # )
    # )


    game = Game('map_config.json')
    game.run()
