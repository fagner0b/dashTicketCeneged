# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a data analysis repository focused on GLPI (IT service management) ticket data. The main data source is `glpi.csv`, which contains ticket information from a Brazilian IT service desk system.

## Data Structure

The primary dataset (`glpi.csv`) contains IT ticket data with the following key fields:
- Ticket ID, Title, Entity, Location
- Status (Pendente, Em atendimento, etc.)
- Opening and last update dates
- Requester and assigned technician
- Category and priority information
- SLA tracking (time for response/resolution)
- Department information

The data uses semicolon (`;`) as delimiter and appears to be in Portuguese.

## Working with the Data

- The CSV uses semicolon separators, not commas
- Date format appears to be DD-MM-YYYY HH:MM
- Text encoding may require UTF-8 handling due to Portuguese characters
- Status values are in Portuguese (e.g., "Pendente", "Em atendimento")

## Common Data Analysis Tasks

When working with this ticket data, common operations include:
- Filtering by status, priority, or department
- Analyzing response times and SLA compliance
- Grouping tickets by technician or category
- Time-based analysis of ticket creation patterns