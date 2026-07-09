#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMU Plot Generator Script

This script reads IMU data from a CSV file and generates plots.
It can be called from the C++ node or used standalone.

Usage:
    python3 imu_plot_generator.py --csv <csv_file> --output <output_dir> [--format png] [--dpi 150]
"""

import argparse
import os
import csv
from datetime import datetime

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np


def load_csv_data(csv_file):
    """Load IMU data from CSV file"""
    timestamps = []
    roll_data = []
    pitch_data = []
    yaw_data = []
    gyr_x_data = []
    gyr_y_data = []
    gyr_z_data = []
    acc_x_data = []
    acc_y_data = []
    acc_z_data = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamps.append(float(row['timestamp']))
            roll_data.append(float(row['roll']))
            pitch_data.append(float(row['pitch']))
            yaw_data.append(float(row['yaw']))
            gyr_x_data.append(float(row['gyr_x']))
            gyr_y_data.append(float(row['gyr_y']))
            gyr_z_data.append(float(row['gyr_z']))
            acc_x_data.append(float(row['acc_x']))
            acc_y_data.append(float(row['acc_y']))
            acc_z_data.append(float(row['acc_z']))

    return {
        'timestamps': np.array(timestamps),
        'roll': np.array(roll_data),
        'pitch': np.array(pitch_data),
        'yaw': np.array(yaw_data),
        'gyr_x': np.array(gyr_x_data),
        'gyr_y': np.array(gyr_y_data),
        'gyr_z': np.array(gyr_z_data),
        'acc_x': np.array(acc_x_data),
        'acc_y': np.array(acc_y_data),
        'acc_z': np.array(acc_z_data),
    }


def generate_plots(data, output_dir, save_format='png', dpi=150):
    """Generate and save plots from IMU data"""
    # Normalize timestamps to start from 0
    timestamps = data['timestamps'] - data['timestamps'][0]

    # Create figure with 3 subplots
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), dpi=dpi)

    # Plot orientation
    ax = axes[0]
    ax.plot(timestamps, data['roll'], 'r-', label='Roll', linewidth=1.5)
    ax.plot(timestamps, data['pitch'], 'g-', label='Pitch', linewidth=1.5)
    ax.plot(timestamps, data['yaw'], 'b-', label='Yaw', linewidth=1.5)
    ax.set_ylabel('Angle (deg)', fontsize=11)
    ax.set_title('Orientation (Euler Angles)', fontsize=12)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)

    # Plot angular velocity
    ax = axes[1]
    ax.plot(timestamps, data['gyr_x'], 'r-', label='X', linewidth=1.5)
    ax.plot(timestamps, data['gyr_y'], 'g-', label='Y', linewidth=1.5)
    ax.plot(timestamps, data['gyr_z'], 'b-', label='Z', linewidth=1.5)
    ax.set_ylabel('Angular Velocity (rad/s)', fontsize=11)
    ax.set_title('Gyroscope', fontsize=12)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)

    # Plot acceleration
    ax = axes[2]
    ax.plot(timestamps, data['acc_x'], 'r-', label='X', linewidth=1.5)
    ax.plot(timestamps, data['acc_y'], 'g-', label='Y', linewidth=1.5)
    ax.plot(timestamps, data['acc_z'], 'b-', label='Z', linewidth=1.5)
    ax.set_ylabel('Acceleration (m/s²)', fontsize=11)
    ax.set_xlabel('Time (s)', fontsize=11)
    ax.set_title('Accelerometer', fontsize=12)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)

    # Update title with current time
    fig.suptitle(f'IMU Data - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                 fontsize=14, fontweight='bold')

    plt.tight_layout()

    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f'imu_plot.{save_format}')
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)

    print(f'Plot saved to: {filepath}')
    return filepath


def main():
    parser = argparse.ArgumentParser(description='Generate IMU plots from CSV data')
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--format', default='png', help='Output format (png, pdf, svg)')
    parser.add_argument('--dpi', type=int, default=150, help='DPI for output image')

    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f'Error: CSV file not found: {args.csv}')
        return 1

    data = load_csv_data(args.csv)
    generate_plots(data, args.output, args.format, args.dpi)

    return 0


if __name__ == '__main__':
    exit(main())