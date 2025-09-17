import fs from 'fs';
import yaml from 'js-yaml';

// This stuff is terrible and should be in a mini library, sorry.
function text(value) {
  return { type: 'text', value };
}
function link(value, url) {
  return { type: 'link', url, children: [text(value)] };
}
function paragraph(children) {
  return { type: 'paragraph', children };
}
function strong(value) {
  return { type: 'strong', children: [text(value)] };
}
function emphasis(value) {
  return { type: 'emphasis', children: [text(value)] };
}
function image(src, alt) {
  return { type: 'image', url: src, alt };
}
function heading(level, value, children = null) {
  if (children) {
    return { type: 'heading', depth: level, children };
  }
  return { type: 'heading', depth: level, children: [text(value)] };
}
function list(items, ordered = false) {
  return { 
    type: ordered ? 'list' : 'list', 
    ordered,
    children: items.map(item => ({ type: 'listItem', children: [paragraph([text(item)])] }))
  };
}
function container(children, style = {}) {
  return { type: 'container', children, style };
}

// Helper function to create a person's card with image and info
function createPersonCard(person) {
  const personInfoChildren = [];

  // Name heading with optional website link and pronouns
  const nameChildren = [];
  if (person.website) {
    nameChildren.push(link(person.name, person.website));
  } else {
    nameChildren.push(text(person.name));
  }
  
  personInfoChildren.push(heading(3, '', nameChildren));

  // Pronouns
  if (person.pronouns) {
    personInfoChildren.push(paragraph([text(person.pronouns)]));
  }

  // Email
  if (person.email) {
    personInfoChildren.push(paragraph([link(person.email, `mailto:${person.email}`)]));
  }

  // Office Hours
  if (person['office-hours'] && person['office-hours'].length > 0) {
    personInfoChildren.push(paragraph([strong('Office Hours:')]));
    
    // Process office hours with structured format
    const processedHours = person['office-hours'].map(hours => {
      if (typeof hours === 'object' && hours.when) {
        // Structured format: { when, where, link }
        const hoursChildren = [];
        
        // Add the time
        hoursChildren.push(strong(hours.when));
        
        // Add location if provided
        if (hours.where) {
          hoursChildren.push(text(', '));
          hoursChildren.push(text(hours.where));
        }
        
        // Add link if provided
        if (hours.link) {
          hoursChildren.push(text(' ('));
          hoursChildren.push(link('Join', hours.link));
          hoursChildren.push(text(')'));
        }
        
        return { type: 'listItem', children: [paragraph(hoursChildren)] };
      } else if (typeof hours === 'string') {
        // Legacy string format - keep for backward compatibility
        return { type: 'listItem', children: [paragraph([text(hours)])] };
      }
      
      return { type: 'listItem', children: [paragraph([text('Invalid office hours format')])] };
    });
    
    personInfoChildren.push({
      type: 'list',
      ordered: false,
      children: processedHours
    });
  }

  // About Me
  if (person['about-me']) {
    personInfoChildren.push(paragraph([strong('About Me: '), text(person['about-me'])]));
  }

  // Create the layout with image on left and info on right
  if (person.photo) {
    // Create a container with flexbox layout
    return {
      type: 'div',
      class: 'staff-person-card',
      children: [
        // Image on the left
        {
          type: 'div',
          class: 'staff-person-photo',
          children: [
            image(person.photo, `Photo of ${person.name}`)
          ]
        },
        // Info on the right
        {
          type: 'div',
          class: 'staff-person-info',
          children: personInfoChildren
        }
      ]
    };
  } else {
    // If no photo, just use the info without flex layout
    return {
      type: 'div',
      class: 'staff-person-card-no-photo',
      children: personInfoChildren
    };
  }
}

const staffDirective = {
  name: 'staff',
  doc: 'Staff directive presents a listing of staff information based on a YAML file',
  arg: { type: String },
  options: {},
  run(data) {
    const staffList = yaml.load(fs.readFileSync(data.arg).toString());
    
    // Group staff by role
    const staffByRole = {};
    staffList.forEach(person => {
      const role = person.role || 'Staff';
      if (!staffByRole[role]) {
        staffByRole[role] = [];
      }
      staffByRole[role].push(person);
    });

    // Define role order and pluralization
    const roleOrder = ['Instructor', 'Teaching Assistant', 'Tutor'];
    const rolePlurals = {
      'Instructor': 'Instructors',
      'Teaching Assistant': 'Teaching Assistants',
      'Tutor': 'Tutors'
    };

    const children = [];

    // Process each role group
    roleOrder.forEach(role => {
      if (staffByRole[role] && staffByRole[role].length > 0) {
        const roleHeading = staffByRole[role].length === 1 ? role : (rolePlurals[role] || role + 's');
        children.push(heading(2, roleHeading));

        staffByRole[role].forEach(person => {
          children.push(createPersonCard(person));
        });
      }
    });

    // Handle any remaining roles not in the predefined order
    Object.keys(staffByRole).forEach(role => {
      if (!roleOrder.includes(role)) {
        const roleHeading = staffByRole[role].length === 1 ? role : (rolePlurals[role] || role + 's');
        children.push(heading(2, roleHeading));

        staffByRole[role].forEach(person => {
          children.push(createPersonCard(person));
        });
      }
    });

    return children;
  },
};

const plugin = { name: 'Staff Directive', directives: [staffDirective] };

export default plugin;
