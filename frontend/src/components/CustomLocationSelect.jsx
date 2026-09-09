import { useState, useRef, useEffect } from 'react';
import './CustomLocationSelect.css';

const CustomLocationSelect = ({
  value,
  onChange,
  options,
  label,
  disabled,
  placeholder = 'Select location...'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);

  const selectedOption = options.find((opt, idx) => idx === value);
  const displayLabel = selectedOption?.name || placeholder;

  const filteredOptions = options.filter(opt =>
    opt.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (idx) => {
    onChange(idx);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && filteredOptions.length > 0) {
      const selectedIdx = options.indexOf(filteredOptions[0]);
      handleSelect(selectedIdx);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setSearchTerm('');
    }
  };

  return (
    <div className="custom-location-select-wrapper">
      {label && <label className="custom-select-label">{label}</label>}
      <div className="custom-location-select" ref={dropdownRef}>
        <button
          className={`custom-select-trigger ${isOpen ? 'open' : ''}`}
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled}
          type="button"
        >
          <span className="selected-value">{displayLabel}</span>
          <span className="dropdown-icon">▼</span>
        </button>

        {isOpen && (
          <div className="custom-select-dropdown">
            <input
              ref={inputRef}
              type="text"
              className="custom-select-search"
              placeholder="Search locations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
            <div className="custom-select-options">
              {filteredOptions.length > 0 ? (
                filteredOptions.map((opt, displayIdx) => {
                  const actualIdx = options.indexOf(opt);
                  return (
                    <button
                      key={actualIdx}
                      className={`custom-select-option ${
                        actualIdx === value ? 'selected' : ''
                      }`}
                      onClick={() => handleSelect(actualIdx)}
                      type="button"
                    >
                      {opt.name}
                    </button>
                  );
                })
              ) : (
                <div className="custom-select-no-results">
                  No locations found
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomLocationSelect;
