// src/components/LeftNav.js
import React from 'react';
import { Link } from 'react-router-dom';

const LeftNav = ({ selectedIndex, onItemSelected }) => {
  return (
    <nav className="left-nav">
      <div className="logo">
        <h2>Clinical Trial</h2>
        <h2>Eligibility</h2>
      </div>
      <ul>
        <li className={selectedIndex === 0 ? 'active' : ''}>
          <Link to="/dashboard" onClick={() => onItemSelected(0)}>Dashboard</Link>
        </li>
        <li className={selectedIndex === 1 ? 'active' : ''}>
          <Link to="/analysis" onClick={() => onItemSelected(1)}>Analysis</Link>
        </li>
        <li className={selectedIndex === 2 ? 'active' : ''}>
          <Link to="/patients" onClick={() => onItemSelected(2)}>Patients</Link>
        </li>
        <li className={selectedIndex === 3 ? 'active' : ''}>
          <Link to="/trials" onClick={() => onItemSelected(3)}>Trials</Link>
        </li>
        <li className={selectedIndex === 4 ? 'active' : ''}>
          <Link to="/history" onClick={() => onItemSelected(4)}>History</Link>
        </li>
      </ul>
    </nav>
  );
};

export default LeftNav;
